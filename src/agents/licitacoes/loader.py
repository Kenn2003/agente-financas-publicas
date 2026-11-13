from functools import lru_cache
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[3]
ARQUIVO = RAIZ / "data/raw/csv/atual_licitacoes.csv"


@lru_cache(maxsize=1)
def carregar_licitacoes():
    """Carrega a base atual de licitações de Palmas-TO."""

    df = pd.read_csv(
        ARQUIVO,
        low_memory=False,
    )

    colunas_numericas = [
        "ano",
        "numero",
        "orgao_id",
        "valor_estimado",
        "valor_homologado",
    ]

    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce",
        )

    colunas_datas = [
        "data_publicacao",
        "data_homologacao",
        "data_abertura",
    ]

    for coluna in colunas_datas:
        df[coluna] = pd.to_datetime(
            df[coluna],
            errors="coerce",
        )

    return df
