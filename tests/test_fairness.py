
"""Testes automatizados das metricas de fairness — Sprint 05."""

import pytest

from src.governance.fairness import (
    avaliar_fairness,
    divisao_segura,
)


def test_paridade_perfeita():
    resultado = avaliar_fairness(
        [1, 1, 0, 0, 1, 1, 0, 0],
        [1, 0, 1, 0, 1, 0, 1, 0],
        ["A"] * 4 + ["B"] * 4,
    )

    assert resultado["demographic_parity_difference"] == 0
    assert resultado["equal_opportunity_difference"] == 0
    assert resultado["disparate_impact_ratio"] == 1
    assert resultado["false_positive_rate_difference"] == 0
    assert resultado["false_negative_rate_difference"] == 0


def test_disparidade_entre_grupos():
    resultado = avaliar_fairness(
        [1, 1, 0, 0, 1, 1, 0, 0],
        [1, 1, 1, 0, 1, 0, 0, 0],
        ["A"] * 4 + ["B"] * 4,
    )

    assert resultado["demographic_parity_difference"] == pytest.approx(0.5)
    assert resultado["equal_opportunity_difference"] == pytest.approx(0.5)
    assert resultado["disparate_impact_ratio"] == pytest.approx(1 / 3)
    assert resultado["false_positive_rate_difference"] == pytest.approx(0.5)
    assert resultado["false_negative_rate_difference"] == pytest.approx(0.5)


def test_acuracia_igual_nao_implica_paridade():
    resultado = avaliar_fairness(
        [1, 1, 0, 0, 1, 1, 0, 0],
        [1, 1, 1, 0, 1, 0, 0, 0],
        ["A"] * 4 + ["B"] * 4,
    )

    a, b = resultado["grupos"]

    assert a["acuracia"] == b["acuracia"] == 0.75
    assert resultado["equal_opportunity_difference"] > 0


def test_matriz_confusao():
    resultado = avaliar_fairness(
        [1, 1, 0, 0],
        [1, 0, 1, 0],
        ["A"] * 4,
    )

    grupo = resultado["grupos"][0]

    assert grupo["tp"] == 1
    assert grupo["tn"] == 1
    assert grupo["fp"] == 1
    assert grupo["fn"] == 1
    assert grupo["n"] == 4


def test_tres_grupos():
    resultado = avaliar_fairness(
        [1, 0, 1, 0, 1, 0],
        [1, 1, 1, 0, 0, 0],
        ["A", "A", "B", "B", "C", "C"],
    )

    assert len(resultado["grupos"]) == 3
    assert resultado["demographic_parity_difference"] == 1
    assert resultado["disparate_impact_ratio"] == 0


def test_grupo_unico():
    resultado = avaliar_fairness(
        [1, 0],
        [1, 0],
        ["A", "A"],
    )

    assert resultado["demographic_parity_difference"] is None
    assert resultado["equal_opportunity_difference"] is None
    assert resultado["disparate_impact_ratio"] is None
    assert resultado["false_positive_rate_difference"] is None
    assert resultado["false_negative_rate_difference"] is None


def test_sem_positivos_reais():
    resultado = avaliar_fairness(
        [0, 0, 1, 0],
        [0, 1, 1, 0],
        ["A", "A", "B", "B"],
    )

    assert resultado["grupos"][0]["tpr"] is None
    assert resultado["equal_opportunity_difference"] is None


def test_sem_negativos_reais():
    resultado = avaliar_fairness(
        [1, 1, 1, 0],
        [1, 0, 1, 0],
        ["A", "A", "B", "B"],
    )

    assert resultado["grupos"][0]["fpr"] is None
    assert resultado["false_positive_rate_difference"] is None


def test_sem_previsoes_positivas():
    resultado = avaliar_fairness(
        [1, 0, 1, 0],
        [0, 0, 0, 0],
        ["A", "A", "B", "B"],
    )

    assert resultado["demographic_parity_difference"] == 0
    assert resultado["disparate_impact_ratio"] is None
    assert resultado["grupos"][0]["precisao"] is None


def test_amostra_vazia():
    with pytest.raises(ValueError):
        avaliar_fairness([], [], [])


def test_tamanhos_diferentes():
    with pytest.raises(ValueError):
        avaliar_fairness([1, 0], [1], ["A", "B"])


@pytest.mark.parametrize("valor", [2, -1, None, "invalido"])
def test_rotulo_invalido(valor):
    with pytest.raises(ValueError):
        avaliar_fairness([valor], [1], ["A"])


@pytest.mark.parametrize("valor", [2, -1, None, "invalido"])
def test_previsao_invalida(valor):
    with pytest.raises(ValueError):
        avaliar_fairness([1], [valor], ["A"])


@pytest.mark.parametrize("grupo", [None, "", " ", 123])
def test_grupo_invalido(grupo):
    with pytest.raises(ValueError):
        avaliar_fairness([1], [1], [grupo])


def test_divisao_por_zero():
    assert divisao_segura(1, 0) is None


def test_divisao_valida():
    assert divisao_segura(1, 2) == 0.5


def test_reprodutibilidade():
    argumentos = (
        [1, 0, 1, 0],
        [1, 1, 0, 0],
        ["A", "A", "B", "B"],
    )

    assert avaliar_fairness(*argumentos) == avaliar_fairness(*argumentos)


def test_finalidade_experimental():
    resultado = avaliar_fairness([1], [1], ["A"])

    assert resultado["finalidade"] == "diagnostico_experimental"
