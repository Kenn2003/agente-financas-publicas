from types import SimpleNamespace

from src.agents.receitas.agent import mensagem_erro_agente


def test_erro_quota_429():
    erro = SimpleNamespace(
        code=429,
        status="RESOURCE_EXHAUSTED"
    )

    mensagem = mensagem_erro_agente(erro)

    assert "limite de solicitações" in mensagem
    assert "Tente novamente" in mensagem


def test_erro_generico():
    erro = RuntimeError("Erro interno de comunicação")

    mensagem = mensagem_erro_agente(erro)

    assert "Não foi possível concluir" in mensagem
    assert "Erro interno de comunicação" not in mensagem


def test_erro_quota_por_mensagem():
    erro = RuntimeError(
        "429 RESOURCE_EXHAUSTED"
    )

    mensagem = mensagem_erro_agente(erro)

    assert "limite de solicitações" in mensagem
    

from types import SimpleNamespace

from src.agents.receitas.agent import (
    extrair_resposta_textual,
)


def criar_resposta(*partes):
    return SimpleNamespace(
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(
                    parts=list(partes)
                )
            )
        ]
    )


def test_resposta_textual_valida():
    resposta = criar_resposta(
        SimpleNamespace(
            text="Arrecadação: R$ 868.065,05",
            function_call=None
        )
    )

    resultado = extrair_resposta_textual(resposta)

    assert resultado == "Arrecadação: R$ 868.065,05"


def test_function_call_pendente():
    resposta = criar_resposta(
        SimpleNamespace(
            text=None,
            function_call=SimpleNamespace(
                name="consultar_receitas"
            )
        )
    )

    resultado = extrair_resposta_textual(resposta)

    assert "não foi concluída" in resultado
    assert "ferramenta" in resultado


def test_resposta_sem_candidatos():
    resposta = SimpleNamespace(candidates=[])

    resultado = extrair_resposta_textual(resposta)

    assert "não pôde ser concluída" in resultado


def test_resposta_sem_texto():
    resposta = criar_resposta(
        SimpleNamespace(
            text=None,
            function_call=None
        )
    )

    resultado = extrair_resposta_textual(resposta)

    assert "não produziu uma resposta textual" in resultado

