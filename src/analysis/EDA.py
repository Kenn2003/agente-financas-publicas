from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ / "saida_eda"
SAIDA.mkdir(parents=True, exist_ok=True)


def localizar_divida_ativa():
    candidatos = [
        RAIZ / "relatorio_dívida_ativa.csv",
        RAIZ / "relatorio_d#U00edvida_ativa.csv",
    ]

    for caminho in candidatos:
        if caminho.exists():
            return caminho

    encontrados = list(RAIZ.glob("*vida_ativa.csv")) + list(RAIZ.glob("*ativa.csv"))

    if encontrados:
        return encontrados[0]

    raise FileNotFoundError(
        "Arquivo de dívida ativa não encontrado. "
        "Coloque o CSV na mesma pasta do EDA.py."
    )


def carregar_dados():
    caminho = localizar_divida_ativa()

    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig"
    )

    colunas = [
        "Nome",
        "Valor Total da Dívida",
        "Data da Inscrição"
    ]

    faltantes = [c for c in colunas if c not in df.columns]

    if faltantes:
        raise ValueError(f"Colunas ausentes: {faltantes}")

    df["Valor Total da Dívida"] = pd.to_numeric(
        df["Valor Total da Dívida"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    df["Data da Inscrição"] = pd.to_datetime(
        df["Data da Inscrição"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "Nome",
            "Valor Total da Dívida",
            "Data da Inscrição"
        ]
    )

    duplicados = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()

    data_referencia = pd.Timestamp.today().normalize()

    df["dias_desde_inscricao"] = (
        data_referencia - df["Data da Inscrição"]
    ).dt.days

    df["mes_inscricao"] = (
        df["Data da Inscrição"]
        .dt.to_period("M")
        .astype(str)
    )

    faixas = [
        0,
        200,
        500,
        1000,
        5000,
        10000,
        50000,
        100000,
        np.inf
    ]

    rotulos = [
        "Até R$ 200",
        "R$ 200–500",
        "R$ 500–1 mil",
        "R$ 1–5 mil",
        "R$ 5–10 mil",
        "R$ 10–50 mil",
        "R$ 50–100 mil",
        "Acima de R$ 100 mil"
    ]

    df["faixa_valor"] = pd.cut(
        df["Valor Total da Dívida"],
        bins=faixas,
        labels=rotulos,
        include_lowest=True
    )

    return df, caminho, duplicados


def grafico_evolucao_quantidade(df):
    mensal = (
        df.groupby("mes_inscricao")
        .size()
        .reset_index(name="quantidade")
        .sort_values("mes_inscricao")
    )

    plt.figure(figsize=(10, 5))
    plt.bar(mensal["mes_inscricao"], mensal["quantidade"])
    plt.title("Quantidade de inscrições em dívida ativa por mês")
    plt.xlabel("Mês de inscrição")
    plt.ylabel("Quantidade de registros")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(SAIDA / "01_evolucao_quantidade_mes.png", dpi=160)
    plt.close()

    return mensal


def grafico_evolucao_valor(df):
    mensal = (
        df.groupby("mes_inscricao")["Valor Total da Dívida"]
        .sum()
        .reset_index(name="valor_total")
        .sort_values("mes_inscricao")
    )

    plt.figure(figsize=(10, 5))
    plt.bar(mensal["mes_inscricao"], mensal["valor_total"])
    plt.title("Valor total inscrito em dívida ativa por mês")
    plt.xlabel("Mês de inscrição")
    plt.ylabel("Valor total (R$)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(SAIDA / "02_evolucao_valor_mes.png", dpi=160)
    plt.close()

    return mensal


def grafico_composicao(df):
    composicao = (
        df.groupby("faixa_valor", observed=False)
        .agg(
            quantidade=("Valor Total da Dívida", "size"),
            valor_total=("Valor Total da Dívida", "sum")
        )
        .reset_index()
    )

    composicao["percentual_registros"] = (
        composicao["quantidade"] / len(df) * 100
    )

    composicao["percentual_valor"] = (
        composicao["valor_total"]
        / df["Valor Total da Dívida"].sum()
        * 100
    )

    plt.figure(figsize=(11, 5))
    plt.bar(
        composicao["faixa_valor"].astype(str),
        composicao["quantidade"]
    )
    plt.title("Composição da dívida ativa por faixa de valor")
    plt.xlabel("Faixa de valor")
    plt.ylabel("Quantidade de registros")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(SAIDA / "03_composicao_faixa_valor.png", dpi=160)
    plt.close()

    composicao.to_csv(
        SAIDA / "composicao_faixas.csv",
        index=False,
        encoding="utf-8-sig"
    )

    return composicao


def grafico_distribuicao(df):
    valores = df["Valor Total da Dívida"]

    plt.figure(figsize=(7, 6))
    plt.boxplot(valores, vert=True)
    plt.yscale("log")
    plt.title("Distribuição dos valores da dívida ativa")
    plt.ylabel("Valor da dívida (R$) — escala logarítmica")
    plt.tight_layout()
    plt.savefig(SAIDA / "04_distribuicao_valores.png", dpi=160)
    plt.close()


def grafico_relacao(df):
    plt.figure(figsize=(9, 6))
    plt.scatter(
        df["dias_desde_inscricao"],
        df["Valor Total da Dívida"],
        alpha=0.20,
        s=8
    )
    plt.yscale("log")
    plt.title("Relação entre tempo desde a inscrição e valor da dívida")
    plt.xlabel("Dias desde a inscrição")
    plt.ylabel("Valor da dívida (R$) — escala logarítmica")
    plt.tight_layout()
    plt.savefig(SAIDA / "05_relacao_tempo_valor.png", dpi=160)
    plt.close()


def salvar_resumo(df, caminho, duplicados, mensal_qtd, mensal_valor, composicao):
    valores = df["Valor Total da Dívida"]

    maior_mes_qtd = mensal_qtd.loc[
        mensal_qtd["quantidade"].idxmax()
    ]

    maior_mes_valor = mensal_valor.loc[
        mensal_valor["valor_total"].idxmax()
    ]

    faixa_alta = composicao[
        composicao["faixa_valor"].astype(str) == "Acima de R$ 100 mil"
    ].iloc[0]

    correlacao = df[
        ["dias_desde_inscricao", "Valor Total da Dívida"]
    ].corr(method="spearman").iloc[0, 1]

    texto = f"""
EDA - DIVIDA ATIVA DE PALMAS

Arquivo analisado: {caminho.name}
Registros tratados: {len(df)}
Duplicatas removidas: {duplicados}

Valor total: R$ {valores.sum():,.2f}
Media: R$ {valores.mean():,.2f}
Mediana: R$ {valores.median():,.2f}
Maior valor: R$ {valores.max():,.2f}

LEITURAS

1. Mes com mais inscricoes:
{maior_mes_qtd["mes_inscricao"]} - {int(maior_mes_qtd["quantidade"])} registros.

2. Mes com maior valor total:
{maior_mes_valor["mes_inscricao"]} - R$ {maior_mes_valor["valor_total"]:,.2f}.

3. Dividas acima de R$ 100 mil:
{faixa_alta["percentual_registros"]:.2f}% dos registros concentram
{faixa_alta["percentual_valor"]:.2f}% do valor total.

4. Distribuicao:
A media e maior que a mediana, indicando presenca de valores muito altos.

5. Relacao entre tempo e valor:
Correlacao de Spearman = {correlacao:.3f}.
"""

    (SAIDA / "resumo_eda.txt").write_text(
        texto,
        encoding="utf-8"
    )


def main():
    df, caminho, duplicados = carregar_dados()

    print("Arquivo:", caminho)
    print("Registros tratados:", len(df))
    print("Duplicatas removidas:", duplicados)

    mensal_qtd = grafico_evolucao_quantidade(df)
    mensal_valor = grafico_evolucao_valor(df)
    composicao = grafico_composicao(df)

    grafico_distribuicao(df)
    grafico_relacao(df)

    salvar_resumo(
        df,
        caminho,
        duplicados,
        mensal_qtd,
        mensal_valor,
        composicao
    )

    print("EDA concluido.")
    print("Arquivos salvos em:", SAIDA)


if __name__ == "__main__":
    main()
