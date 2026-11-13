from pathlib import Path
from functools import lru_cache

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

CSV_PATH = PROJECT_ROOT / "relatorio_dívida_ativa.csv"


@lru_cache(maxsize=1)
def carregar_divida_ativa() -> pd.DataFrame:

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Base de dívida ativa não encontrada: {CSV_PATH}"
        )

    df = pd.read_csv(
        CSV_PATH,
        sep=";",
        encoding="utf-8-sig",
        usecols=[
            "Valor Total da Dívida",
            "Data da Inscrição"
        ]
    )

    df["valor_divida"] = pd.to_numeric(
        df["Valor Total da Dívida"]
        .astype(str)
        .str.replace("R$", "", regex=False)
        .str.strip()
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    df["data_inscricao"] = pd.to_datetime(
        df["Data da Inscrição"],
        dayfirst=True,
        errors="coerce"
    )

    df["ano"] = df["data_inscricao"].dt.year
    df["mes"] = df["data_inscricao"].dt.month

    return df[
        [
            "valor_divida",
            "data_inscricao",
            "ano",
            "mes"
        ]
    ].copy()