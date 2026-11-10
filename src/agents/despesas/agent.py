import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .prompts import SYSTEM_PROMPT
from .tools import (
    consultar_execucao,
    consultar_execucao_empenho,
    rastrear_empenho,
)
from src.agents.despesas.loader_atual import (
    consultar_execucao_atual,
    rastrear_empenho_atual
    )


RAIZ = Path(__file__).resolve().parents[3]

load_dotenv(RAIZ / ".env")

def consultar_despesas_atuais(ano: int) -> dict:
    """
    Consulta os totais de empenhos, liquidações e pagamentos
    de Palmas-TO nos exercícios de 2022 a 2026.

    Args:
        ano: Exercício solicitado, entre 2022 e 2026.

    Returns:
        Totais de execução orçamentária e limitações da base.
    """
    print(f"[TOOL] consultar_despesas_atuais(ano={ano})")

    return consultar_execucao_atual(ano)

def consultar_empenho_atual(
    ano: int,
    orgao: int,
    empenho: int
) -> dict:
    """
    Rastreia um empenho municipal entre 2022 e 2026.

    Args:
        ano: Exercício do empenho.
        orgao: Código do órgão responsável pelo empenho.
        empenho: Número do empenho.

    Returns:
        Valores empenhados, liquidados e pagos,
        além da quantidade de movimentações.
    """
    print(
        f"[TOOL] consultar_empenho_atual("
        f"ano={ano}, orgao={orgao}, empenho={empenho})"
    )

    return rastrear_empenho_atual(
        ano=ano,
        orgao=orgao,
        empenho=empenho
    )

FERRAMENTAS = [
    consultar_execucao_atual,
    consultar_empenho_atual,
    consultar_execucao,
    consultar_execucao_empenho,
    rastrear_empenho,
]

class AgenteDespesas:
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
                    maximum_remote_calls=4
                )
            ),
            temperature=0.1,
        )

        # Mantém o histórico durante a sessão.
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

        except Exception as erro:
            return (
                "Não foi possível processar a consulta. "
                f"Detalhes técnicos: {erro}"
            )
