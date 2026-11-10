import pandas as pd

from src.agents.licitacoes.loader import carregar_licitacoes


def _filtrar(
    ano=None,
    modalidade=None,
    orgao=None,
    situacao=None,
):
    df = carregar_licitacoes()

    if ano is not None:
        df = df[df["ano"] == int(ano)]

    if modalidade:
        df = df[
            df["modalidade"].fillna("").str.casefold()
            == modalidade.casefold()
        ]

    if orgao:
        df = df[
            df["orgao"].fillna("")
            .str.contains(orgao, case=False, regex=False)
        ]

    if situacao:
        df = df[
            df["situacao"].fillna("").str.casefold()
            == situacao.casefold()
        ]

    return df


def _numero(valor):
    if pd.isna(valor):
        return None
    return round(float(valor), 2)


def _registro(linha):
    return {
        "chave": int(linha["chave"]),
        "numero": int(linha["numero"]),
        "ano": int(linha["ano"]),
        "modalidade": linha["modalidade"],
        "situacao": linha["situacao"],
        "orgao": linha["orgao"],
        "valor_estimado": _numero(linha["valor_estimado"]),
        "valor_homologado": _numero(linha["valor_homologado"]),
        "descricao": linha["descricao"],
    }


def consultar_licitacoes(
    ano: int | None = None,
    modalidade: str | None = None,
    orgao: str | None = None,
    situacao: str | None = None,
    limite: int = 20,
) -> dict:
    """Consulta licitações com filtros combináveis."""

    if limite < 1:
        raise ValueError("limite deve ser positivo")

    df = _filtrar(ano, modalidade, orgao, situacao)

    return {
        "status": "ok",
        "total_encontrado": len(df),
        "resultados_limitados": len(df) > limite,
        "licitacoes": [
            _registro(linha)
            for _, linha in df.head(limite).iterrows()
        ],
        "fonte": "atual_licitacoes.csv",
    }


def resumir_licitacoes(ano: int) -> dict:
    """Resume as licitações de determinado exercício."""

    df = _filtrar(ano=ano)

    if df.empty:
        return {"status": "sem_dados", "ano": ano}

    return {
        "status": "ok",
        "ano": ano,
        "quantidade": len(df),
        "homologadas": int(
            df["situacao"].eq("Homologada").sum()
        ),
        "valor_estimado": _numero(
            df["valor_estimado"].sum(min_count=1)
        ),
        "valor_homologado": _numero(
            df["valor_homologado"].sum(min_count=1)
        ),
        "sem_valor_estimado": int(
            df["valor_estimado"].isna().sum()
        ),
        "sem_valor_homologado": int(
            df["valor_homologado"].isna().sum()
        ),
        "fonte": "atual_licitacoes.csv",
        "observacao": (
            "Somas dos valores informados na base. "
            "Não representam necessariamente despesas "
            "executadas nem economia obtida."
        ),
    }


def comparar_modalidades(ano: int) -> dict:
    """Compara modalidades licitatórias por exercício."""

    df = _filtrar(ano=ano)

    if df.empty:
        return {"status": "sem_dados", "ano": ano}

    resumo = (
        df.groupby("modalidade", dropna=False)
        .agg(
            quantidade=("chave", "count"),
            valor_estimado=(
                "valor_estimado",
                lambda s: s.sum(min_count=1)
            ),
            valor_homologado=(
                "valor_homologado",
                lambda s: s.sum(min_count=1)
            ),
            sem_valor_homologado=(
                "valor_homologado",
                lambda x: int(x.isna().sum())
            ),
        )
        .reset_index()
        .sort_values("quantidade", ascending=False)
    )

    modalidades = []

    for _, linha in resumo.iterrows():
        modalidades.append({
            "modalidade": (
                None if pd.isna(linha["modalidade"])
                else linha["modalidade"]
            ),
            "quantidade": int(linha["quantidade"]),
            "valor_estimado": _numero(
                linha["valor_estimado"]
            ),
            "valor_homologado": _numero(
                linha["valor_homologado"]
            ),
            "sem_valor_homologado": int(
                linha["sem_valor_homologado"]
            ),
        })

    return {
        "status": "ok",
        "ano": ano,
        "modalidades": modalidades,
        "fonte": "atual_licitacoes.csv",
    }


def consultar_licitacao(
    numero: int,
    ano: int,
) -> dict:
    """
    Localiza licitações por número e ano.
    Pode retornar múltiplos registros.
    """

    df = _filtrar(ano=ano)
    df = df[df["numero"] == int(numero)]

    if df.empty:
        return {
            "status": "sem_dados",
            "numero": numero,
            "ano": ano,
        }

    return {
        "status": "ok",
        "numero": numero,
        "ano": ano,
        "quantidade": len(df),
        "licitacoes": [
            _registro(linha)
            for _, linha in df.iterrows()
        ],
        "fonte": "atual_licitacoes.csv",
    }


def consultar_licitacao_por_chave(chave: int) -> dict:
    """Consulta um processo licitatório pela chave única."""

    df = carregar_licitacoes()

    resultado = df.loc[df["chave"] == int(chave)]

    if resultado.empty:
        return {
            "status": "sem_dados",
            "chave": chave,
        }

    linha = resultado.iloc[0]

    return {
        "status": "ok",
        "licitacao": _registro(linha),
        "fonte": "atual_licitacoes.csv",
    }

