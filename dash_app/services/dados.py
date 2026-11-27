"""Leitura e preparação segura das séries agregadas usadas no dashboard."""
from functools import lru_cache
from pathlib import Path

import pandas as pd


RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_DADOS = RAIZ_PROJETO / "data" / "ready"
CODIGOS_TOTAL_RECEITA = {
    "1.0.0.0.00.0.0",
    "2.0.0.0.00.0.0",
    "7.0.0.0.00.0.0",
    "8.0.0.0.00.0.0",
}
COLUNAS_DESPESA = ["valor_empenho", "valor_liq", "valor_pago"]


class ErroDadosDash(ValueError):
    """Erro de leitura ou de esquema, adequado para exibição controlada."""


def preparar_receitas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza receitas para os códigos agregados usados no Streamlit atual."""
    necessarias = {"ano", "mes", "codigo", "valor_arrecado_mes"}
    faltantes = sorted(necessarias.difference(df.columns))
    if faltantes:
        raise ErroDadosDash("Colunas ausentes na base de receitas: " + ", ".join(faltantes))

    dados = df[["ano", "mes", "codigo", "valor_arrecado_mes"]].copy()
    dados["codigo"] = dados["codigo"].astype("string").str.strip()
    for coluna in ("ano", "mes", "valor_arrecado_mes"):
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")

    dados = dados.dropna(subset=["ano", "mes", "valor_arrecado_mes"])
    dados = dados.loc[dados["codigo"].isin(CODIGOS_TOTAL_RECEITA)].copy()
    dados = dados.loc[dados["mes"].between(1, 12)].copy()
    dados["ano"] = dados["ano"].astype(int)
    dados["mes"] = dados["mes"].astype(int)
    return dados.reset_index(drop=True)


def preparar_despesas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza os valores agregáveis sem descartar lançamentos negativos."""
    necessarias = {"ano_referencia", *COLUNAS_DESPESA}
    faltantes = sorted(necessarias.difference(df.columns))
    if faltantes:
        raise ErroDadosDash("Colunas ausentes na base de despesas: " + ", ".join(faltantes))

    dados = df[["ano_referencia", *COLUNAS_DESPESA]].copy()
    dados["ano_referencia"] = pd.to_numeric(dados["ano_referencia"], errors="coerce")
    for coluna in COLUNAS_DESPESA:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
    dados = dados.dropna(subset=["ano_referencia"])
    dados["ano_referencia"] = dados["ano_referencia"].astype(int)
    return dados.reset_index(drop=True)


@lru_cache(maxsize=1)
def carregar_receitas() -> pd.DataFrame:
    caminho = PASTA_DADOS / "receitas_recentes.parquet"
    if not caminho.is_file():
        raise ErroDadosDash("Não foi encontrado data/ready/receitas_recentes.parquet.")
    try:
        df = pd.read_parquet(
            caminho,
            columns=["ano", "mes", "codigo", "valor_arrecado_mes"],
        )
    except Exception as erro:
        raise ErroDadosDash(
            "A base de receitas não pôde ser lida. Confira o arquivo e a dependência Parquet."
        ) from erro
    return preparar_receitas(df)


@lru_cache(maxsize=1)
def carregar_despesas() -> pd.DataFrame:
    caminho = PASTA_DADOS / "gastos_diretos.parquet"
    if not caminho.is_file():
        raise ErroDadosDash("Não foi encontrado data/ready/gastos_diretos.parquet.")
    try:
        df = pd.read_parquet(
            caminho,
            columns=["ano_referencia", *COLUNAS_DESPESA],
        )
    except Exception as erro:
        raise ErroDadosDash(
            "A base de despesas não pôde ser lida. Confira o arquivo e a dependência Parquet."
        ) from erro
    return preparar_despesas(df)


def agregar_receitas(df: pd.DataFrame, ano: int, meses=None) -> pd.DataFrame:
    dados = df.loc[df["ano"] == int(ano)]
    if meses is not None:
        meses_validos = [int(mes) for mes in meses if 1 <= int(mes) <= 12]
        dados = dados.loc[dados["mes"].isin(meses_validos)]
    return (
        dados.groupby("mes", as_index=False)["valor_arrecado_mes"]
        .sum(min_count=1)
        .sort_values("mes")
        .reset_index(drop=True)
    )


def agregar_despesas_anuais(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("ano_referencia", as_index=False)[COLUNAS_DESPESA]
        .sum(min_count=1)
        .sort_values("ano_referencia")
        .reset_index(drop=True)
    )
