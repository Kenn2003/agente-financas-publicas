from functools import lru_cache
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[3]

ARQUIVO = (
    RAIZ / "data" / "raw" / "csv" / "atual_contratos.csv"
)

TIPOS_VALIDOS = {"Contrato", "Aditivo", "Distrato"}

COLUNAS_DATAS = (
    "data_firmatura",
    "inicio_vigencia",
    "fim_vigencia",
    "data_publicacao",
)


@lru_cache(maxsize=1)
def carregar_contratos():
    if not ARQUIVO.is_file():
        raise FileNotFoundError(
            f"Base de contratos não encontrada: {ARQUIVO}"
        )

    df = pd.read_csv(
        ARQUIVO,
        low_memory=False,
        dtype={
            "id": "string",
            "chave_contrato": "string",
        },
    )

    for coluna in COLUNAS_DATAS:
        df[coluna] = pd.to_datetime(
            df[coluna],
            errors="coerce",
        )

    df["valor"] = pd.to_numeric(
        df["valor"],
        errors="coerce",
    )

    if df["id"].isna().any():
        raise ValueError("Existem registros sem ID.")

    if df["id"].duplicated().any():
        raise ValueError("Existem IDs duplicados.")

    if df["chave_contrato"].isna().any():
        raise ValueError("Existem contratos sem chave.")

    tipos = set(df["tipo"].dropna().unique())

    if not tipos.issubset(TIPOS_VALIDOS):
        raise ValueError(
            f"Tipos contratuais desconhecidos: "
            f"{tipos - TIPOS_VALIDOS}"
        )

    originais = df[df["tipo"] == "Contrato"]

    if originais["chave_contrato"].duplicated().any():
        raise ValueError(
            "Existem contratos originais com chave duplicada."
        )

    eventos = df[df["tipo"] != "Contrato"]

    chaves_originais = set(
        originais["chave_contrato"]
    )

    orfaos = ~eventos["chave_contrato"].isin(
        chaves_originais
    )

    if orfaos.any():
        raise ValueError(
            f"Existem {orfaos.sum()} eventos "
            "sem contrato original."
        )

    return df
