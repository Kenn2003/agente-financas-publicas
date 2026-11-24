
"""Evidencias experimentais de fairness — Sprint 05."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.governance.fairness import avaliar_fairness


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/evidencias/fairness"
OUTPUT.mkdir(parents=True, exist_ok=True)


def gerar_cenarios():
    y_true = [1, 1, 0, 0, 1, 1, 0, 0]
    grupos = ["A"] * 4 + ["B"] * 4

    cenarios = {
        "paridade": [1, 0, 1, 0, 1, 0, 1, 0],
        "disparidade": [1, 1, 1, 0, 1, 0, 0, 0],
        "paridade_selecao_sem_equal_opportunity": [
            1, 1, 0, 0, 0, 0, 1, 1
        ],
    }

    resultados = {
        nome: avaliar_fairness(y_true, pred, grupos)
        for nome, pred in cenarios.items()
    }

    relatorio = {
        "natureza": "dados_integralmente_sinteticos",
        "aviso": (
            "Grupos ficticios, sem correspondencia com "
            "contribuintes ou territorios reais."
        ),
        "cenarios": resultados,
    }

    (OUTPUT / "cenarios_sinteticos.json").write_text(
        json.dumps(
            relatorio,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    return resultados


def grafico_modelos(relatorio):
    nomes = {
        "regressao_logistica": "Regressão Logística",
        "arvore_decisao": "Árvore de Decisão",
        "random_forest_inadimplencia": "Random Forest",
    }

    linhas = []

    for chave, nome in nomes.items():
        dados = relatorio["modelos"][chave]["faixa_valor"]

        linhas.append({
            "Modelo": nome,
            "Demographic Parity": (
                dados["demographic_parity_difference"]
            ),
            "Equal Opportunity": (
                dados["equal_opportunity_difference"]
            ),
            "Diferença de FPR": (
                dados["false_positive_rate_difference"]
            ),
        })

    tabela = pd.DataFrame(linhas).set_index("Modelo")

    ax = tabela.plot(
        kind="bar",
        figsize=(11, 6),
        color=["#4078B8", "#E5A043", "#438C78"],
        width=0.75,
    )

    ax.set_title(
        "Disparidades experimentais por valor da dívida"
    )
    ax.set_ylabel("Diferença entre taxas")
    ax.set_ylim(0, 1.1)
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", alpha=0.25)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", padding=3)

    plt.figtext(
        0.5, 0.01,
        "Alvos sintéticos — não representa equidade demográfica real.",
        ha="center",
        fontsize=9,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    plt.savefig(
        OUTPUT / "01_comparacao_modelos.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()


def grafico_random_forest(relatorio):
    grupos = relatorio["modelos"][
        "random_forest_inadimplencia"
    ]["faixa_valor"]["grupos"]

    tabela = pd.DataFrame(grupos).set_index("grupo")

    tabela = tabela.reindex([
        "ate_500",
        "500_a_5000",
        "acima_5000",
    ])

    tabela.index = [
        "Até R$ 500",
        "R$ 500 a R$ 5.000",
        "Acima de R$ 5.000",
    ]

    dados = tabela[["taxa_selecao", "tpr", "fpr"]] * 100

    dados.columns = [
        "Taxa de seleção",
        "Verdadeiros positivos (TPR)",
        "Falsos positivos (FPR)",
    ]

    ax = dados.plot(
        kind="bar",
        figsize=(12, 6),
        color=["#4078B8", "#438C78", "#C45D5D"],
    )

    ax.set_title(
        "Random Forest — métricas por faixa de dívida"
    )
    ax.set_ylabel("Percentual (%)")
    ax.set_ylim(0, 110)
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", alpha=0.25)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.1f%%", padding=3)

    plt.figtext(
        0.5, 0.01,
        "Diagnóstico experimental com rótulos sintéticos.",
        ha="center",
        fontsize=9,
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    plt.savefig(
        OUTPUT / "02_random_forest_subgrupos.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()


def grafico_cenarios(cenarios):
    linhas = []

    for nome, resultado in cenarios.items():
        linhas.append({
            "Cenário": nome,
            "DP Difference": (
                resultado["demographic_parity_difference"]
            ),
            "EO Difference": (
                resultado["equal_opportunity_difference"]
            ),
            "DI Ratio": (
                resultado["disparate_impact_ratio"]
            ),
        })

    tabela = pd.DataFrame(linhas).set_index("Cenário")

    tabela.index = [
        "Paridade",
        "Disparidade",
        "DP sem EO",
    ]

    ax = tabela.plot(
        kind="bar",
        figsize=(10, 6),
        color=["#4078B8", "#E5A043", "#438C78"],
    )

    ax.set_title("Demonstração com grupos fictícios")
    ax.set_ylim(0, 1.1)
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", alpha=0.25)

    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", padding=3)

    plt.tight_layout()

    plt.savefig(
        OUTPUT / "03_cenarios_sinteticos.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close()


def exportar_metricas(relatorio):
    linhas = []

    for modelo, dimensoes in relatorio["modelos"].items():
        for dimensao, resultado in dimensoes.items():
            for grupo in resultado["grupos"]:
                linhas.append({
                    "modelo": modelo,
                    "dimensao": dimensao,
                    **grupo,
                })

    pd.DataFrame(linhas).to_csv(
        OUTPUT / "metricas_por_subgrupo.csv",
        index=False,
        encoding="utf-8-sig",
    )


def executar():
    relatorio = json.loads(
        (OUTPUT / "metricas_modelos_proxy.json").read_text(
            encoding="utf-8"
        )
    )

    cenarios = gerar_cenarios()

    grafico_modelos(relatorio)
    grafico_random_forest(relatorio)
    grafico_cenarios(cenarios)
    exportar_metricas(relatorio)

    print("Evidencias de fairness geradas com sucesso.")

    for nome, resultado in cenarios.items():
        print(
            nome,
            "DP:", resultado["demographic_parity_difference"],
            "EO:", resultado["equal_opportunity_difference"],
            "DI:", resultado["disparate_impact_ratio"],
        )

    print("\nArquivos gerados:")

    for arquivo in sorted(OUTPUT.glob("*")):
        print(arquivo.name)


if __name__ == "__main__":
    executar()
