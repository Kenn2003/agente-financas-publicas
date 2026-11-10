import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors


from src.agents.licitacoes.prompts import SYSTEM_PROMPT

from src.agents.licitacoes.tools import (
    consultar_licitacoes,
    resumir_licitacoes,
    comparar_modalidades,
    consultar_licitacao_por_chave,
)

from src.agents.licitacoes.auditoria import (
    auditar_valores_licitacoes,
    analisar_impacto_registro,
)


RAIZ = Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")


FERRAMENTAS = [
    consultar_licitacoes,
    resumir_licitacoes,
    comparar_modalidades,
    consultar_licitacao_por_chave,
    auditar_valores_licitacoes,
    analisar_impacto_registro,
]


class AgenteLicitacoes:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY não configurada no .env"
            )

        self.modelo = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

        self.client = genai.Client(api_key=api_key)

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
            config=self.config
        )
    
    def responder(self, pergunta: str) -> str:
    
        if not isinstance(pergunta, str):
            raise ValueError(
                "A pergunta precisa ser uma string."
            )
    
        pergunta = pergunta.strip()
    
        if not pergunta:
            raise ValueError(
                "A pergunta não pode estar vazia."
            )
    
        try:
            resposta = self.chat.send_message(pergunta)
    
            if resposta.text:
                return resposta.text
    
            return (
                "O modelo não produziu uma resposta "
                "textual para esta consulta."
            )
    
        except errors.ClientError as erro:
    
            if erro.code == 429:
                return (
                    "O limite temporário de requisições "
                    "da API Gemini foi atingido. "
                    "Aguarde o período indicado pela API "
                    "antes de realizar outra consulta."
                )
    
            return (
                "Erro ao consultar a API Gemini. "
                f"Código HTTP: {erro.code}"
            )
    
        except Exception as erro:
            return (
                "Não foi possível processar a consulta. "
                f"Detalhes técnicos: {erro}"
            )


