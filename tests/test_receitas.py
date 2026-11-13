import pytest

from src.agents.receitas.tools import (
    consultar_receitas,
    buscar_orgaos,
)

import pandas as pd
from unittest.mock import patch
from src.agents.receitas import tools as receitas_tools


@pytest.mark.parametrize(
    "codigo, valor_esperado",
    [
        (1200, 868065.05),
        (7500, 92.82),
    ],
)
def test_arrecadacao_por_codigo(codigo, valor_esperado):
    resultado = consultar_receitas(
        ano=2024,
        mes=3,
        codigo_orgao=codigo,
    )

    assert resultado["status"] == "ok"
    assert resultado["valor_arrecadado"] == pytest.approx(
        valor_esperado,
        abs=0.01,
    )


def test_orgao_inexistente():
    resultado = consultar_receitas(
        ano=2024,
        mes=3,
        codigo_orgao=999999,
    )

    assert resultado["status"] == "sem_dados"


def test_periodo_futuro_sem_dados():
    resultado = consultar_receitas(
        ano=2030,
        mes=3,
    )

    assert resultado["status"] == "sem_dados"


def test_busca_orgaos_por_ano():
    resultado = buscar_orgaos(
        termo="Mobilidade",
        ano=2024,
    )

    codigos = {
        int(orgao["orgao"])
        for orgao in resultado["orgaos"]
    }

    assert resultado["status"] == "ok"
    assert 1200 in codigos
    assert 7500 in codigos
    assert 1202 not in codigos


def test_consulta_por_nome():
    resultado = consultar_receitas(
        ano=2024,
        mes=3,
        orgao=(
            "SECRETARIA MUNICIPAL DE SEGURANCA "
            "E MOBILIDADE URBANA"
        ),
    )

    assert resultado["status"] == "ok"
    assert resultado["valor_arrecadado"] == pytest.approx(
        868065.05,
        abs=0.01,
    )
    


def test_arrecadacao_zero_com_registro():
    dados = pd.DataFrame([
        {
            "ano": 2024,
            "mes": 3,
            "orgao": 1200,
            "orgao_nome": "SECRETARIA TESTE",
            "codigo": "1.0.0.0.00.0.0",
            "valor_arrecado_mes": 0.0,
        }
    ])

    with patch.object(
        receitas_tools,
        "carregar_receitas",
        return_value=dados
    ):
        resultado = receitas_tools.consultar_receitas(
            ano=2024,
            mes=3,
            codigo_orgao=1200
        )

    assert resultado["status"] == "ok"
    assert resultado["valor_arrecadado"] == 0.0


def test_sem_registros_nao_retorna_zero():
    resultado = receitas_tools.consultar_receitas(
        ano=2024,
        mes=3,
        codigo_orgao=999999
    )

    assert resultado["status"] == "sem_dados"
    assert "valor_arrecadado" not in resultado

