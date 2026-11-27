import pandas as pd

from dash_app.services.dados import (
    ErroDadosDash,
    agregar_despesas_anuais,
    agregar_receitas,
    preparar_despesas,
    preparar_receitas,
)


def test_preparar_receitas_filtra_codigo_agregado_e_mes_invalido():
    bruto = pd.DataFrame({
        "ano": [2025, 2025, 2025],
        "mes": [1, 13, 2],
        "codigo": ["1.0.0.0.00.0.0", "1.0.0.0.00.0.0", "999"],
        "valor_arrecado_mes": [100.0, 999.0, 500.0],
    })
    pronto = preparar_receitas(bruto)
    assert pronto[["ano", "mes", "valor_arrecado_mes"]].to_dict("records") == [
        {"ano": 2025, "mes": 1, "valor_arrecado_mes": 100.0}
    ]


def test_agregar_receitas_filtra_periodo_e_mantem_soma():
    dados = preparar_receitas(pd.DataFrame({
        "ano": [2025, 2025],
        "mes": [1, 2],
        "codigo": ["1.0.0.0.00.0.0", "1.0.0.0.00.0.0"],
        "valor_arrecado_mes": [100.0, 250.0],
    }))
    assert agregar_receitas(dados, 2025, [2])["valor_arrecado_mes"].tolist() == [250.0]


def test_preparar_despesas_preserva_valor_negativo():
    bruto = pd.DataFrame({
        "ano_referencia": [2024, 2024],
        "valor_empenho": [10.0, -2.0],
        "valor_liq": [8.0, -1.0],
        "valor_pago": [5.0, 0.0],
    })
    anual = agregar_despesas_anuais(preparar_despesas(bruto))
    linha = anual.iloc[0]
    assert linha["valor_empenho"] == 8.0
    assert linha["valor_liq"] == 7.0
    assert linha["valor_pago"] == 5.0


def test_preparar_receitas_rejeita_esquema_incompleto():
    try:
        preparar_receitas(pd.DataFrame({"ano": [2025]}))
    except ErroDadosDash as erro:
        assert "Colunas ausentes" in str(erro)
    else:
        raise AssertionError("Esperava erro de esquema")
