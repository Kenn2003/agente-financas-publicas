from dataclasses import replace
from decimal import Decimal

import pytest

from src.governance.iptu_social import (
    DadosContribuinte,
    SituacaoBeneficio,
    DecisaoGovernanca,
    Elegibilidade,
    avaliar_protecao_iptu_social
)


# ==================================================
# 1. FIXTURES
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
# 2. PROTEÇÃO ADMINISTRATIVA
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
def test_beneficiario_reconhecido(
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

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.decisao == (
        DecisaoGovernanca.BLOQUEAR
    )


# ==================================================
# 3. CATEGORIAS PESSOAIS PROTEGIDAS
# ==================================================

@pytest.mark.parametrize(
    "categoria",
    [
        {"idade": 66},
        {"aposentado": True},
        {"pensionista": True},
        {"deficiencia_fisica_incapacitante": True}
    ]
)
def test_categorias_potencialmente_elegiveis(
    contribuinte_base,
    categoria
):

    dados = replace(
        contribuinte_base,
        **categoria
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.elegibilidade_pessoal == (
        Elegibilidade.SIM
    )

    assert resultado.decisao == (
        DecisaoGovernanca.REVISAO_HUMANA
    )


# ==================================================
# 4. LIMITE DE IDADE
# ==================================================

@pytest.mark.parametrize(
    "idade, esperado",
    [
        (64, Elegibilidade.NAO),
        (65, Elegibilidade.NAO),
        (66, Elegibilidade.SIM),
        (80, Elegibilidade.SIM)
    ]
)
def test_limite_idade(
    contribuinte_base,
    idade,
    esperado
):

    dados = replace(
        contribuinte_base,
        idade=idade
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.elegibilidade_pessoal == esperado


# ==================================================
# 5. LIMITE DE RENDA
# ==================================================

@pytest.mark.parametrize(
    "renda, esperado",
    [
        ("0", Elegibilidade.SIM),
        ("1.99", Elegibilidade.SIM),
        ("2.00", Elegibilidade.SIM),
        ("2.01", Elegibilidade.NAO),
        ("5.00", Elegibilidade.NAO)
    ]
)
def test_limite_renda(
    contribuinte_base,
    renda,
    esperado
):

    dados = replace(
        contribuinte_base,
        idade=70,
        renda_mensal_sm=Decimal(renda)
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.elegibilidade_pessoal == esperado


# ==================================================
# 6. LIMITE DE 150 UFIP
# ==================================================

@pytest.mark.parametrize(
    "iptu, esperado",
    [
        ("149.99", Elegibilidade.SIM),
        ("150.00", Elegibilidade.NAO),
        ("150.01", Elegibilidade.NAO)
    ]
)
def test_limite_iptu_pessoal(
    contribuinte_base,
    iptu,
    esperado
):

    dados = replace(
        contribuinte_base,
        idade=70,
        iptu_bruto_ufip=Decimal(iptu)
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.elegibilidade_pessoal == esperado


# ==================================================
# 7. LIMITE DE 50 UFIP
# ==================================================

@pytest.mark.parametrize(
    "iptu, esperado",
    [
        ("0", Elegibilidade.SIM),
        ("49.99", Elegibilidade.SIM),
        ("50.00", Elegibilidade.NAO),
        ("50.01", Elegibilidade.NAO)
    ]
)
def test_limite_iptu_automatico(
    contribuinte_base,
    iptu,
    esperado
):

    dados = replace(
        contribuinte_base,
        iptu_bruto_ufip=Decimal(iptu)
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.elegibilidade_automatica == esperado

    if esperado == Elegibilidade.SIM:

        assert resultado.decisao == (
            DecisaoGovernanca.REVISAO_HUMANA
        )


# ==================================================
# 8. REQUISITOS IMOBILIÁRIOS
# ==================================================

@pytest.mark.parametrize(
    "alteracao",
    [
        {
            "quantidade_imoveis": 2,
            "quantidade_imoveis_edificados": 2
        },
        {"quantidade_edificacoes": 2},
        {"uso_exclusivamente_residencial": False},
        {"garagem_ou_box_autonomo": True},
        {"pessoa_fisica": False}
    ]
)
def test_requisitos_isencao_automatica(
    contribuinte_base,
    alteracao
):

    dados = replace(
        contribuinte_base,
        iptu_bruto_ufip=Decimal("40"),
        **alteracao
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.elegibilidade_automatica == (
        Elegibilidade.NAO
    )


# ==================================================
# 9. DADOS AUSENTES
# ==================================================

@pytest.mark.parametrize(
    "campo",
    [
        "renda_mensal_sm",
        "quantidade_imoveis_edificados",
        "uso_exclusivamente_residencial",
        "iptu_bruto_ufip"
    ]
)
def test_dados_ausentes(
    contribuinte_base,
    campo
):

    dados = replace(
        contribuinte_base,
        idade=70,
        **{campo: None}
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.decisao == (
        DecisaoGovernanca.REVISAO_HUMANA
    )


def test_contribuinte_sem_informacoes():

    dados = DadosContribuinte(exercicio=2026)

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.decisao == (
        DecisaoGovernanca.REVISAO_HUMANA
    )


# ==================================================
# 10. DADOS INVÁLIDOS
# ==================================================

@pytest.mark.parametrize(
    "alteracao",
    [
        {"idade": -1},
        {"idade": True},
        {"quantidade_imoveis": -2},
        {"quantidade_imoveis_edificados": 5},
        {"renda_mensal_sm": Decimal("-1")},
        {"renda_mensal_sm": Decimal("NaN")},
        {"renda_mensal_sm": Decimal("Infinity")},
        {"iptu_bruto_ufip": Decimal("-10")},
        {"aposentado": "sim"},
        {"renda_mensal_sm": 1.5}
    ]
)
def test_dados_invalidos(
    contribuinte_base,
    alteracao
):

    dados = replace(
        contribuinte_base,
        **alteracao
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.decisao == (
        DecisaoGovernanca.REVISAO_HUMANA
    )


# ==================================================
# 11. SEGURANÇA DECISÓRIA
# ==================================================

@pytest.mark.parametrize(
    "situacao",
    [
        SituacaoBeneficio.PENDENTE,
        SituacaoBeneficio.DESCONHECIDO
    ]
)
def test_situacao_administrativa_nao_resolvida(
    contribuinte_base,
    situacao
):

    dados = replace(
        contribuinte_base,
        situacao_beneficio=situacao
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.decisao == (
        DecisaoGovernanca.REVISAO_HUMANA
    )


@pytest.mark.parametrize(
    "situacao",
    list(SituacaoBeneficio)
)
def test_dados_nao_verificados(
    contribuinte_base,
    situacao
):

    dados = replace(
        contribuinte_base,
        dados_oficiais_verificados=False,
        situacao_beneficio=situacao
    )

    resultado = avaliar_protecao_iptu_social(dados)

    assert resultado.decisao == (
        DecisaoGovernanca.REVISAO_HUMANA
    )


def test_contribuinte_sem_enquadramento(
    contribuinte_base
):

    resultado = avaliar_protecao_iptu_social(
        contribuinte_base
    )

    assert resultado.elegibilidade_pessoal == (
        Elegibilidade.NAO
    )

    assert resultado.elegibilidade_automatica == (
        Elegibilidade.NAO
    )

    assert resultado.decisao == (
        DecisaoGovernanca.PROSSEGUIR
    )


# ==================================================
# 12. DETERMINISMO
# ==================================================

def test_determinismo(contribuinte_base):

    resultados = [
        avaliar_protecao_iptu_social(contribuinte_base)
        for _ in range(100)
    ]

    assert all(
        resultado == resultados[0]
        for resultado in resultados
    )
