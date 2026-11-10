import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.agents.receitas.prompts import SYSTEM_PROMPT
from src.agents.receitas import tools as receitas_tools


# Localiza o .env na raiz do projeto
RAIZ = Path(__file__).resolve().parents[3]
load_dotenv(RAIZ / ".env")

MODELO = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# FERRAMENTAS EXPOSTAS AO GEMINI

def consultar_receitas(
    ano: int,
    mes: Optional[int] = None,
    orgao: Optional[str] = None,
    codigo_orgao: Optional[int] = None
) -> dict:

    print(
        f"[TOOL] consultar_receitas("
        f"ano={ano}, mes={mes}, "
        f"orgao={orgao}, codigo_orgao={codigo_orgao})"
    )

    return receitas_tools.consultar_receitas(
        ano=ano,
        mes=mes,
        orgao=orgao,
        codigo_orgao=codigo_orgao
    )

def evolucao_arrecadacao(
    ano: int,
    orgao: Optional[str] = None
) -> dict:
    """
    Obtém a série mensal de arrecadação.

    Args:
        ano: Ano desejado, entre 2021 e 2026.
        orgao: Nome completo do órgão. Opcional.

    Returns:
        Série mensal com valores arrecadados.
    """
    
    print(f"[TOOL] evolucao_arrecadacao(ano={ano}, orgao={orgao})")
    
    return receitas_tools.evolucao_arrecadacao(
        ano=ano,
        orgao=orgao
    )


def comparar_periodos(
    ano_inicial: int,
    ano_final: int,
    orgao: Optional[str] = None
) -> dict:
    """
    Compara a arrecadação entre dois anos.

    Args:
        ano_inicial: Primeiro ano da comparação.
        ano_final: Segundo ano da comparação.
        orgao: Nome completo do órgão. Opcional.

    Returns:
        Totais, meses comparados e variação nominal.
    """
    
    print(
        f"[TOOL] comparar_periodos("
        f"ano_inicial={ano_inicial}, "
        f"ano_final={ano_final}, orgao={orgao})"
    )    
    
    return receitas_tools.comparar_periodos(
        ano_inicial=ano_inicial,
        ano_final=ano_final,
        orgao=orgao
    )

def buscar_orgaos(termo: str, ano: Optional[int] = None) -> dict:
    """Localiza nomes oficiais de órgãos por palavra ou trecho."""
    print(f"[TOOL] buscar_orgaos(termo={termo}, ano={ano})")
    return receitas_tools.buscar_orgaos(termo = termo, ano=ano)

def agrupar_receitas(
    ano: int,
    agrupamento: str = "tributo",
    mes: Optional[int] = None,
    somente_principal: bool = False,
) -> dict:
    """Agrupa IPTU, ISS, ITBI e IRRF por códigos validados de 2024.

    Args:
        ano: Exercício da arrecadação; atualmente apenas 2024.
        agrupamento: Tipo de agrupamento; atualmente 'tributo'.
        mes: Mês de referência opcional (1 a 12).
        somente_principal: Restringe a arrecadação ao principal,
            quando houver código validado para o tributo.

    Returns:
        Totais por tributo e indicação de limitações de cobertura.
    """
    print(
        f"[TOOL] agrupar_receitas(ano={ano}, "
        f"agrupamento={agrupamento}, mes={mes}, "
        f"somente_principal={somente_principal})"
    )
    return receitas_tools.agrupar_receitas(
        ano=ano,
        agrupamento=agrupamento,
        mes=mes,
        somente_principal=somente_principal,
    )


def mensagem_erro_agente(erro):
    """Converte erros da API em mensagens controladas."""

    codigo = getattr(erro, "code", None)
    status = getattr(erro, "status", None)

    if (
        codigo == 429
        or status == "RESOURCE_EXHAUSTED"
        or "RESOURCE_EXHAUSTED" in str(erro)
    ):
        return (
            "O serviço de inteligência artificial atingiu "
            "o limite de solicitações disponível. "
            "Tente novamente após a renovação da quota."
        )

    return (
        "Não foi possível concluir a consulta devido "
        "a um erro no serviço de inteligência artificial."
    )


def extrair_resposta_textual(resposta):
    """Extrai texto e identifica respostas incompletas."""

    candidatos = getattr(resposta, "candidates", None) or []

    if not candidatos:
        return (
            "O modelo não retornou uma resposta válida. "
            "A consulta não pôde ser concluída."
        )

    conteudo = getattr(candidatos[0], "content", None)
    partes = getattr(conteudo, "parts", None) or []

    textos = []
    chamadas_pendentes = False

    for parte in partes:
        texto = getattr(parte, "text", None)
        chamada = getattr(parte, "function_call", None)

        if texto:
            textos.append(texto)

        if chamada is not None:
            chamadas_pendentes = True

    if chamadas_pendentes:
        return (
            "A consulta não foi concluída porque o modelo "
            "solicitou uma chamada adicional de ferramenta."
        )

    if textos:
        return "\n".join(textos)

    return (
        "O modelo não produziu uma resposta textual. "
        "A consulta não pôde ser concluída."
    )


FERRAMENTAS = [
    consultar_receitas,
    evolucao_arrecadacao,
    comparar_periodos,
    buscar_orgaos,
    agrupar_receitas
]


# AGENTE

class AgenteReceitas:

    def __init__(
        self,
        modelo: str = MODELO,
        client=None
    ):
        if client is None:
            chave = os.getenv("GEMINI_API_KEY")

            if not chave:
                raise ValueError(
                    "GEMINI_API_KEY não encontrada. "
                    "Configure o arquivo .env."
                )

            client = genai.Client(api_key=chave)

        self.client = client
        self.modelo = modelo

        self.chat = self.client.chats.create(
            model=self.modelo,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0,
                tools=FERRAMENTAS,
                automatic_function_calling=(
                    types.AutomaticFunctionCallingConfig(
                        maximum_remote_calls=4
                    )
                )
            )
        )

    def responder(self, pergunta: str) -> str:
    
        if not isinstance(pergunta, str):
            raise TypeError("A pergunta deve ser uma string.")
    
        pergunta = pergunta.strip()
    
        if not pergunta:
            raise ValueError("A pergunta não pode estar vazia.")
    
        try:
            resposta = self.chat.send_message(pergunta)
            return extrair_resposta_textual(resposta)
    
        except Exception as erro:
            print(f"[ERRO] {type(erro).__name__}: {erro}")
            return mensagem_erro_agente(erro)

    
    
# TESTE INTERATIVO
def main():
    agente = AgenteReceitas()

    print("=" * 55)
    print("AGENTE DE RECEITAS PÚBLICAS - PALMAS/TO")
    print("Digite 'sair' para encerrar.")
    print("=" * 55)

    while True:
        pergunta = input("\nPergunta: ").strip()

        if pergunta.lower() in {"sair", "exit"}:
            print("Agente encerrado.")
            break

        if not pergunta:
            continue

        try:
            resposta = agente.responder(pergunta)
            print("\nResposta:\n")
            print(resposta)

        except Exception as erro:
            print(f"\nErro: {erro}")


if __name__ == "__main__":
    main()
