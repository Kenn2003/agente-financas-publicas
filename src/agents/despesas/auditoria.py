import pandas as pd

from src.agents.despesas.loader_atual import (
    carregar_despesas_atuais,
)

TOLERANCIA = 0.01


def auditar_empenhos(
    ano: int,
    orgao: int | None = None,
    limite: int = 100,
) -> dict:
    """
    Identifica inconsistências potenciais na execução
    orçamentária, sem concluir pela existência de
    irregularidade administrativa ou contábil.
    """
    if ano not in range(2022, 2027):
        return {
            "status": "ano_nao_suportado",
            "ano": ano,
        }

    if limite < 1:
        raise ValueError("limite deve ser positivo")

    df = carregar_despesas_atuais()

    dados = df.loc[df["ano"] == ano].copy()

    if orgao is not None:
        dados = dados.loc[
            dados["orgao_empenho"] == orgao
        ]

    if dados.empty:
        return {
            "status": "sem_dados",
            "ano": ano,
            "orgao": orgao,
        }

    # Cada empenho pode ter várias movimentações.
    # A combinação evita misturar órgãos diferentes.
    chaves = ["ano", "orgao_empenho", "chave_empenho"]

    tabela = (
        dados.pivot_table(
            index=chaves,
            columns="tipo",
            values="valor",
            aggfunc="sum",
            fill_value=0,
        )
        .rename(
            columns={
                0: "empenhado",
                1: "liquidado",
                2: "pago",
            }
        )
        .reset_index()
    )

    for coluna in ["empenhado", "liquidado", "pago"]:
        if coluna not in tabela.columns:
            tabela[coluna] = 0.0

    alertas = []

    for registro in tabela.to_dict("records"):
        empenhado = float(registro["empenhado"])
        liquidado = float(registro["liquidado"])
        pago = float(registro["pago"])

        ocorrencias = []

        if liquidado > empenhado + TOLERANCIA:
            ocorrencias.append(
                "LIQUIDACAO_SUPERIOR_EMPENHO"
            )

        if pago > liquidado + TOLERANCIA:
            ocorrencias.append(
                "PAGAMENTO_SUPERIOR_LIQUIDACAO"
            )

        if pago > TOLERANCIA and liquidado <= TOLERANCIA:
            ocorrencias.append(
                "PAGAMENTO_SEM_LIQUIDACAO_NA_BASE"
            )

        if liquidado > TOLERANCIA and empenhado <= TOLERANCIA:
            ocorrencias.append(
                "LIQUIDACAO_SEM_EMPENHO_NA_BASE"
            )

        if ocorrencias:
            alertas.append({
                "ano": int(registro["ano"]),
                "orgao": int(registro["orgao_empenho"]),
                "chave_empenho": str(
                    registro["chave_empenho"]
                ),
                "empenhado": round(empenhado, 2),
                "liquidado": round(liquidado, 2),
                "pago": round(pago, 2),
                "alertas": ocorrencias,
            })

    return {
        "status": "ok",
        "ano": ano,
        "orgao": orgao,
        "empenhos_analisados": len(tabela),
        "empenhos_com_alertas": len(alertas),
        "total_alertas": sum(
            len(item["alertas"]) for item in alertas
        ),
        "ocorrencias": alertas[:limite],
        "resultados_limitados": len(alertas) > limite,
        "fonte": "atual_despesas.csv",
        "observacao": (
            "Triagem automatizada preliminar. "
            "Os alertas não comprovam irregularidades. "
            "Cancelamentos, estornos, restos a pagar "
            "e cobertura temporal exigem conciliação."
        ),
    }
