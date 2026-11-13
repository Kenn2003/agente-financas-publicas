import os
import time
import random
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

from .prompts import SYSTEM_PROMPT

from .tools import (
    resumo_divida_ativa,
    divida_por_mes,
    distribuicao_faixas,
    analisar_concentracao,
    consultar_inscricoes,
    auditar_divida_ativa,
)


RAIZ = Path(__file__).resolve().parents[3]

load_dotenv(RAIZ / ".env")

from functools import wraps
import json


def monitorar_ferramenta(funcao):

    @wraps(funcao)
    def executar(*args, **kwargs):

        print(f"\n[TOOL CALL] {funcao.__name__}")
        print(f"[ARGUMENTOS] {args}, {kwargs}")

        resultado = funcao(*args, **kwargs)

        print(
            "[RESULTADO]",
            json.dumps(
                resultado,
                ensure_ascii=False,
                default=str,
            ),
        )

        return resultado

    return executar

FERRAMENTAS = [
    monitorar_ferramenta(resumo_divida_ativa),
    monitorar_ferramenta(divida_por_mes),
    monitorar_ferramenta(distribuicao_faixas),
    monitorar_ferramenta(analisar_concentracao),
    monitorar_ferramenta(consultar_inscricoes),
    monitorar_ferramenta(auditar_divida_ativa),
]

class AgenteDividaAtiva:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY não configurada."
            )

        self.modelo = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash",
        )

        self.client = genai.Client(
            api_key=api_key
        )

        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=FERRAMENTAS,
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    maximum_remote_calls=6
                )
            ),
            temperature=0.1,
        )

        self.chat = self.client.chats.create(
            model=self.modelo,
            config=self.config,
        )


    def responder(self, pergunta: str) -> str:
    
        if not isinstance(pergunta, str):
            raise ValueError("A pergunta deve ser uma string.")
    
        pergunta = pergunta.strip()
    
        if not pergunta:
            return "Informe uma pergunta válida."
    
        max_tentativas = 3
    
        for tentativa in range(max_tentativas):
    
            try:
                resposta = self.chat.send_message(pergunta)
    
                return (
                    resposta.text
                    or "O modelo não produziu uma resposta."
                )
    
            except (errors.ClientError, errors.ServerError) as erro:
    
                codigo = getattr(erro, "code", None)
    
                if codigo in (429, 503):
    
                    if tentativa < max_tentativas - 1:
                        espera = (2 ** (tentativa + 1)) + random.uniform(0, 1)
    
                        print(
                            f"API Gemini indisponível ({codigo}). "
                            f"Nova tentativa em {espera:.1f}s."
                        )
    
                        time.sleep(espera)
                        continue
    
                    return (
                        f"Não foi possível concluir a consulta após "
                        f"{max_tentativas} tentativas. "
                        f"Erro da API Gemini: {codigo}."
                    )
    
                return (
                    "Não foi possível processar a consulta. "
                    f"Erro da API Gemini: {codigo}."
                )
    
            except Exception as erro:
                return (
                    "Não foi possível processar a consulta. "
                    f"Detalhes técnicos: {erro}"
                )
# ```

# Essa implementação realiza até três tentativas em erros 429 ou 503, com espera progressiva e pequena variação aleatória.

# Uma ressalva: repetir `send_message` na mesma sessão pode não ser ideal se a requisição anterior tiver sido parcialmente processada. Para consultas estritamente somente de leitura, como as deste agente, o risco é menor; posteriormente podemos implementar uma estratégia de repetição com controle explícito do histórico.

# ## 2. Testar novamente

# Mantenha temporariamente apenas:

# ```python
# FERRAMENTAS = [
#     resumo_divida_ativa,
# ]
# ```

# Reinicie o kernel do Spyder e execute:

# ```python
# %cd C:/Users/kennk/agente-financas-publicas

# from src.agents.divida_ativa.agent import AgenteDividaAtiva

# agente = AgenteDividaAtiva()

# print(
#     agente.responder(
#         "Qual é o valor total da dívida ativa "
#         "e quantos registros existem na base?"
#     )
# )
# ```

# Se o modelo responder corretamente, voltaremos a habilitar as outras ferramentas, uma de cada vez, para identificar quais assinaturas o SDK aceita.

# **Não recomendo modificar novamente `tools.py` por causa do erro 503.** Esse problema é de disponibilidade do serviço, não da implementação das consultas.

# Se o 503 persistir mesmo após as tentativas, o próximo diagnóstico será verificar o modelo configurado em `GEMINI_MODEL` e testar outro modelo disponível para sua chave.
