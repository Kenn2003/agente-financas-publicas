from pathlib import Path
from functools import lru_cache

import pandas as pd


RAIZ = Path(__file__).resolve().parents[3]

ARQUIVO = (
    RAIZ / "data" / "raw" / "csv" / "atual_despesas.csv"
)

TIPOS = {
    0: "Empenho",
    1: "Liquidação",
    2: "Pagamento",
}


@lru_cache(maxsize=1)
def carregar_despesas_atuais():

    colunas = [
        "chave_empenho",
        "ano",
        "tipo",
        "movimento",
        "numero",
        "data",
        "orgao",
        "orgao_empenho",
        "valor",
        "desativado",
    ]

    df = pd.read_csv(
        ARQUIVO,
        usecols=colunas,
        dtype={
            "chave_empenho": "string",
            "numero": "string",
            "movimento": "string",
            "valor": "string",
        },
        low_memory=False,
    )

    df["valor"] = pd.to_numeric(
        df["valor"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )

    df["data"] = pd.to_datetime(
        df["data"],
        dayfirst=True,
        errors="coerce",
    )

    df["ano"] = pd.to_numeric(
        df["ano"], errors="coerce"
    )

    df["tipo"] = pd.to_numeric(
        df["tipo"], errors="coerce"
    )

    df["desativado"] = pd.to_numeric(
        df["desativado"], errors="coerce"
    )

    # Não excluímos empenhos repetidos:
    # cada linha representa uma movimentação.
    df = df[
        (df["ano"].between(2022, 2026))
        & (df["tipo"].isin(TIPOS))
        & (df["desativado"] == 0)
    ].copy()

    return df


def consultar_execucao_atual(ano: int) -> dict:

    df = carregar_despesas_atuais()

    dados = df[df["ano"] == ano]

    if dados.empty:
        return {
            "status": "sem_dados",
            "ano": ano,
        }

    totais = dados.groupby("tipo")["valor"].sum(
        min_count=1
    )

    return {
        "status": "ok",
        "ano": ano,
        "empenhado": round(float(totais.get(0, 0)), 2),
        "liquidado": round(float(totais.get(1, 0)), 2),
        "pago": round(float(totais.get(2, 0)), 2),
        "registros": len(dados),
        "fonte": "atual_despesas.csv",
        "observacao": (
            "Totais preliminares por ano informado "
            "na base, sem conciliação de estornos, "
            "cancelamentos ou restos a pagar."
        ),
    }


def rastrear_empenho_atual(
    ano: int,
    orgao: int,
    empenho: int
) -> dict:

    df = carregar_despesas_atuais()

    # A chave identifica o empenho, mas utilizamos
    # também ano e órgão para restringir a consulta.
    dados = df[
        (df["ano"] == ano)
        & (df["orgao_empenho"] == orgao)
        & (
            df["chave_empenho"]
            .str.startswith(
                f"[{empenho}-",
                na=False
            )
        )
    ].copy()

    if dados.empty:
        return {
            "status": "sem_dados",
            "ano": ano,
            "orgao": orgao,
            "empenho": empenho,
        }

    totais = dados.groupby("tipo")["valor"].sum()

    return {
        "status": "ok",
        "ano": ano,
        "orgao": orgao,
        "empenho": empenho,
        "empenhado": round(float(totais.get(0, 0)), 2),
        "liquidado": round(float(totais.get(1, 0)), 2),
        "pago": round(float(totais.get(2, 0)), 2),
        "movimentacoes": len(dados),
        "fonte": "atual_despesas.csv",
    }
