import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

from .prompts import SYSTEM_PROMPT

from .tools import (
    consultar_contratos,
    resumir_contratos,
    consultar_contrato_por_chave,
)

from .auditoria import (
    analisar_aditivos,
    analisar_vigencias,
    auditar_contratos,
)


RAIZ = Path(__file__).resolve().parents[3]

load_dotenv(RAIZ / ".env")


FERRAMENTAS = [
    consultar_contratos,
    resumir_contratos,
    consultar_contrato_por_chave,
    analisar_aditivos,
    analisar_vigencias,
    auditar_contratos,
]


class AgenteContratos:

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
            raise ValueError(
                "A pergunta deve ser uma string."
            )

        pergunta = pergunta.strip()

        if not pergunta:
            return "Informe uma pergunta válida."

        try:
            resposta = self.chat.send_message(
                pergunta
            )

            return (
                resposta.text
                or "O modelo não produziu uma resposta."
            )

        except errors.ClientError as erro:
            if erro.code == 429:
                return (
                    "O limite temporário de requisições "
                    "da API Gemini foi atingido. "
                    "Aguarde a liberação da cota."
                )

            return (
                "Não foi possível processar a consulta. "
                f"Erro da API: {erro.code}"
            )

        except Exception as erro:
            return (
                "Não foi possível processar a consulta. "
                f"Detalhes técnicos: {erro}"
            )
