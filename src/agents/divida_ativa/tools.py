import pandas as pd

from .loader import carregar_divida_ativa


def _dados():
    # Cópia para não modificar o DataFrame em cache.
    return carregar_divida_ativa().copy()


def resumo_divida_ativa() -> dict:
    df = _dados()
    valores = df["valor_divida"]

    return {
        "registros": int(len(df)),
        "valor_total": round(float(valores.sum()), 2),
        "valor_medio": round(float(valores.mean()), 2),
        "mediana": round(float(valores.median()), 2),
        "valor_minimo": round(float(valores.min()), 2),
        "valor_maximo": round(float(valores.max()), 2),
        "primeira_inscricao": df["data_inscricao"].min().date().isoformat(),
        "ultima_inscricao": df["data_inscricao"].max().date().isoformat(),
        "observacao": (
            "Valores registrados na base disponível; "
            "não representam necessariamente o saldo atualizado."
        ),
    }


def divida_por_mes(ano: int) -> dict:
    df = _dados()
    df = df[df["ano"] == int(ano)]

    resultado = (
        df.groupby("mes")
        .agg(
            registros=("valor_divida", "size"),
            valor_total=("valor_divida", "sum"),
            valor_medio=("valor_divida", "mean"),
        )
        .reset_index()
    )

    return {
        "ano": int(ano),
        "dados": [
            {
                "mes": int(r.mes),
                "registros": int(r.registros),
                "valor_total": round(float(r.valor_total), 2),
                "valor_medio": round(float(r.valor_medio), 2),
            }
            for r in resultado.itertuples(index=False)
        ],
    }


def distribuicao_faixas() -> list[dict]:
    df = _dados()

    limites = [0, 100, 500, 1000, 5000, 10000, 100000, float("inf")]

    rotulos = [
        "Até R$ 100",
        "R$ 100 a R$ 500",
        "R$ 500 a R$ 1.000",
        "R$ 1.000 a R$ 5.000",
        "R$ 5.000 a R$ 10.000",
        "R$ 10.000 a R$ 100.000",
        "Acima de R$ 100.000",
    ]

    df["faixa"] = pd.cut(
        df["valor_divida"],
        bins=limites,
        labels=rotulos,
        include_lowest=True,
    )

    resumo = (
        df.groupby("faixa", observed=True)
        .agg(
            registros=("valor_divida", "size"),
            valor_total=("valor_divida", "sum"),
        )
        .reindex(rotulos, fill_value=0)
    )

    return [
        {
            "faixa": str(faixa),
            "registros": int(linha.registros),
            "valor_total": round(float(linha.valor_total), 2),
        }
        for faixa, linha in resumo.iterrows()
    ]


def analisar_concentracao() -> dict:
    df = _dados()
    valores = df["valor_divida"].sort_values(ascending=False)
    total = float(valores.sum())
    n = len(valores)

    participacoes = {}

    for percentual in [1, 5, 10]:
        quantidade = max(1, (n * percentual + 99) // 100)
        quantidade = int(quantidade)

        soma = float(valores.head(quantidade).sum())

        participacoes[f"top_{percentual}_percentual"] = {
            "registros": quantidade,
            "valor_total": round(soma, 2),
            "participacao_percentual": (
                round(soma / total * 100, 2) if total else 0
            ),
        }

    return {
        "total_registros": n,
        "concentracao": participacoes,
        "observacao": (
            "Concentração por registro, não por contribuinte."
        ),
    }


def consultar_inscricoes(
    periodo_inicio: str,
    periodo_fim: str
) -> dict:
    inicio = pd.to_datetime(periodo_inicio, errors="raise")
    fim = pd.to_datetime(periodo_fim, errors="raise")

    if inicio > fim:
        raise ValueError(
            "A data inicial não pode ser posterior à data final."
        )

    df = _dados()

    filtro = df[
        (df["data_inscricao"] >= inicio)
        & (df["data_inscricao"] < fim + pd.Timedelta(days=1))
    ]

    return {
        "periodo_inicio": inicio.date().isoformat(),
        "periodo_fim": fim.date().isoformat(),
        "registros": int(len(filtro)),
        "valor_total": round(float(filtro["valor_divida"].sum()), 2),
        "valor_medio": (
            round(float(filtro["valor_divida"].mean()), 2)
            if not filtro.empty else None
        ),
    }


def auditar_divida_ativa() -> dict:
    df = _dados()

    duplicatas = int(
        df.duplicated(
            subset=["valor_divida", "data_inscricao"]
        ).sum()
    )

    return {
        "registros": int(len(df)),
        "valores_ausentes": int(df["valor_divida"].isna().sum()),
        "datas_ausentes": int(df["data_inscricao"].isna().sum()),
        "valores_negativos": int((df["valor_divida"] < 0).sum()),
        "valores_zerados": int((df["valor_divida"] == 0).sum()),
        "coincidencias_valor_data": duplicatas,
        "observacao": (
            "Coincidências de valor e data não comprovam duplicidade. "
            "A base original não possui identificador único de inscrição."
        ),
    }
