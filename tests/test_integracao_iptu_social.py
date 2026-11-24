from dataclasses import replace
from decimal import Decimal
import inspect

import pytest

from src.governance.iptu_social import (
    DadosContribuinte,
    SituacaoBeneficio
)

from src.governance.controle_cobranca import (
    verificar_protecao_iptu_social,
    exigir_liberacao_governanca,
    CobrancaNaoAutorizada
)

from src.agents.divida_ativa import tools


# ==================================================
# 1. FIXTURE
# ==================================================

@pytest.fixture
def contribuinte_base():

    return DadosContribuinte(
        exercicio=2026,
        situacao_beneficio=(
            SituacaoBeneficio.NAO_RECONHECIDO
        ),
        dados_oficiais_verificados=True,
        pessoa_fisica=True,
        idade=40,
        aposentado=False,
        pensionista=False,
        deficiencia_fisica_incapacitante=False,
        quantidade_imoveis=1,
        quantidade_imoveis_edificados=1,
        quantidade_edificacoes=1,
        uso_exclusivamente_residencial=True,
        garagem_ou_box_autonomo=False,
        renda_mensal_sm=Decimal("1.5"),
        iptu_bruto_ufip=Decimal("100")
    )


# ==================================================
# 2. INTEGRAÇÃO COM AS FERRAMENTAS
# ==================================================

def test_ferramenta_disponivel():

    assert callable(
        tools.verificar_protecao_iptu_social
    )


def test_integracao_motor_governanca():

    resultado = tools.verificar_protecao_iptu_social(
        2026
    )

    assert resultado["decisao"] == "revisao_humana"
    assert resultado["cobranca_autorizada"] is False
    assert resultado["dados_oficiais_verificados"] is False

    assert resultado["elegibilidade_pessoal"] == (
        "indeterminada"
    )

    assert resultado["elegibilidade_automatica"] == (
        "indeterminada"
    )


def test_fundamentacao_legal_disponivel():

    resultado = verificar_protecao_iptu_social(2026)

    assert "285/2013" in resultado["fundamento_legal"]
    assert "art. 20" in resultado["fundamento_legal"]


# ==================================================
# 3. EXERCÍCIOS FORA DO ESCOPO
# ==================================================

@pytest.mark.parametrize(
    "exercicio",
    [
        2024,
        2025,
        2027,
        2030,
        -1,
        None,
        "2026",
        True,
        2026.0
    ]
)
def test_exercicio_invalido(exercicio):

    resultado = verificar_protecao_iptu_social(
        exercicio
    )

    assert resultado["decisao"] == "revisao_humana"
    assert resultado["cobranca_autorizada"] is False


# ==================================================
# 4. PROTEÇÃO CONTRA MANIPULAÇÃO
# ==================================================

def test_assinatura_restrita():

    parametros = inspect.signature(
        tools.verificar_protecao_iptu_social
    ).parameters

    assert list(parametros) == ["exercicio"]


@pytest.mark.parametrize(
    "argumentos",
    [
        {"dados_oficiais_verificados": True},
        {"situacao_beneficio": "nao_reconhecido"},
        {"cobranca_autorizada": True},
        {"idade": 40},
        {"renda_mensal_sm": 10},
        {"ignorar_governanca": True}
    ]
)
def test_injecao_argumentos_nao_autorizados(
    argumentos
):

    with pytest.raises(TypeError):

        tools.verificar_protecao_iptu_social(
            2026,
            **argumentos
        )


# ==================================================
# 5. BENEFICIÁRIOS PROTEGIDOS
# ==================================================

@pytest.mark.parametrize(
    "categoria",
    [
        {"idade": 75},
        {"aposentado": True},
        {"pensionista": True},
        {"deficiencia_fisica_incapacitante": True},
        {}
    ]
)
def test_bloqueio_beneficiarios(
    contribuinte_base,
    categoria
):

    dados = replace(
        contribuinte_base,
        situacao_beneficio=(
            SituacaoBeneficio.RECONHECIDO
        ),
        **categoria
    )

    with pytest.raises(CobrancaNaoAutorizada):

        exigir_liberacao_governanca(dados)


# ==================================================
# 6. POSSÍVEIS BENEFICIÁRIOS
# ==================================================

@pytest.mark.parametrize(
    "alteracao",
    [
        {"idade": 70},
        {"aposentado": True},
        {"pensionista": True},
        {"deficiencia_fisica_incapacitante": True},
        {"iptu_bruto_ufip": Decimal("40")}
    ]
)
def test_bloqueio_potenciais_beneficiarios(
    contribuinte_base,
    alteracao
):

    dados = replace(
        contribuinte_base,
        **alteracao
    )

    with pytest.raises(CobrancaNaoAutorizada):

        exigir_liberacao_governanca(dados)


# ==================================================
# 7. AUSÊNCIA DE COMPROVAÇÃO OFICIAL
# ==================================================

@pytest.mark.parametrize(
    "situacao",
    list(SituacaoBeneficio)
)
def test_bloqueio_sem_verificacao(
    contribuinte_base,
    situacao
):

    dados = replace(
        contribuinte_base,
        dados_oficiais_verificados=False,
        situacao_beneficio=situacao
    )

    with pytest.raises(CobrancaNaoAutorizada):

        exigir_liberacao_governanca(dados)


def test_bloqueio_sem_dados_cadastrais():

    dados = DadosContribuinte(
        exercicio=2026
    )

    with pytest.raises(CobrancaNaoAutorizada):

        exigir_liberacao_governanca(dados)


# ==================================================
# 8. SITUAÇÕES ADMINISTRATIVAS PENDENTES
# ==================================================

@pytest.mark.parametrize(
    "situacao",
    [
        SituacaoBeneficio.PENDENTE,
        SituacaoBeneficio.DESCONHECIDO
    ]
)
def test_bloqueio_situacao_pendente(
    contribuinte_base,
    situacao
):

    dados = replace(
        contribuinte_base,
        situacao_beneficio=situacao
    )

    with pytest.raises(CobrancaNaoAutorizada):

        exigir_liberacao_governanca(dados)


# ==================================================
# 9. VALIDAÇÃO DO EXERCÍCIO NA BARREIRA
# ==================================================

@pytest.mark.parametrize(
    "exercicio",
    [
        2025,
        2027,
        None,
        True,
        "2026",
        2026.0
    ]
)
def test_barreira_exercicio_invalido(
    contribuinte_base,
    exercicio
):

    dados = replace(
        contribuinte_base,
        exercicio=exercicio
    )

    with pytest.raises(CobrancaNaoAutorizada):

        exigir_liberacao_governanca(dados)


# ==================================================
# 10. PROSSEGUIMENTO CONTROLADO
# ==================================================

def test_prosseguimento_demais_controles(
    contribuinte_base
):

    resultado = exigir_liberacao_governanca(
        contribuinte_base
    )

    assert resultado is None


# ==================================================
# 11. OPERAÇÃO ADVERSA SIMULADA
# ==================================================

def test_operacao_bloqueada_antes_execucao():

    operacoes_executadas = []

    def operacao_simulada(dados):

        exigir_liberacao_governanca(dados)

        operacoes_executadas.append(
            "operacao_executada"
        )

    dados = DadosContribuinte(
        exercicio=2026
    )

    with pytest.raises(CobrancaNaoAutorizada):

        operacao_simulada(dados)

    assert operacoes_executadas == []


def test_operacao_simulada_liberada(
    contribuinte_base
):

    operacoes_executadas = []

    def operacao_simulada(dados):

        exigir_liberacao_governanca(dados)

        operacoes_executadas.append(
            "demais_controles"
        )

    operacao_simulada(contribuinte_base)

    assert operacoes_executadas == [
        "demais_controles"
    ]
