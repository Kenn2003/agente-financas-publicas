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


RAIZ = Path(__file__).resolve().parents[3]

load_dotenv(RAIZ / ".env")


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
            tools=[
                consultar_execucao,
                consultar_execucao_empenho,
                rastrear_empenho,
            ],
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
