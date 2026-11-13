from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
ENTRADA = RAIZ / "data" / "processed" / "gastos_diretos.csv"
SAIDA = RAIZ / "data" / "processed" / "despesas"

SAIDA.mkdir(parents=True, exist_ok=True)

CHAVE_EMPENHO = [
    "ano_referencia", "cod_unidade", "empenho"
]

CHAVE_LIQUIDACAO = CHAVE_EMPENHO + ["liquidacao"]

CHAVE_PAGAMENTO = CHAVE_LIQUIDACAO + ["numero_pagamento"]


def carregar_dados():
    df = pd.read_csv(ENTRADA, low_memory=False)

    if df["id"].duplicated().any():
        raise ValueError("Existem IDs de origem duplicados.")

    return df


def consolidar_empenhos(df):
    grupos = df.groupby(
        CHAVE_EMPENHO, dropna=False
    )

    empenhos = grupos.agg(
        quantidade_registros=("id", "size"),
        valor_empenho_min=("valor_empenho", "min"),
        valor_empenho_max=("valor_empenho", "max"),
        valores_distintos=("valor_empenho", "nunique"),
        registros_anulacao=("valor_anulado", lambda x: (x != 0).sum())
    ).reset_index()

    empenhos["valor_empenho"] = (
        empenhos["valor_empenho_min"].where(
            empenhos["valores_distintos"] == 1
        )
    )

    empenhos["status"] = "consistente"

    empenhos.loc[
        empenhos["valores_distintos"] > 1,
        "status"
    ] = "valor_empenho_divergente"

    return empenhos


def consolidar_liquidacoes(df):
    dados = df.loc[
        df["liquidacao"] != 0
    ].copy()

    liquidacoes = dados.groupby(
        CHAVE_LIQUIDACAO, dropna=False
    ).agg(
        quantidade_registros=("id", "size"),
        valor_liq_soma_linhas=("valor_liq", "sum"),
        valores_distintos=("valor_liq", "nunique"),
        data_liquidacao_min=("data_liquidacao", "min"),
        data_liquidacao_max=("data_liquidacao", "max")
    ).reset_index()

    liquidacoes["status"] = "revisao_granularidade"

    return liquidacoes


def consolidar_pagamentos(df):
    dados = df.loc[
        (df["numero_pagamento"] != 0) &
        (df["data_pagamento"].notna())
    ].copy()

    pagamentos = dados.groupby(
        CHAVE_PAGAMENTO, dropna=False
    ).agg(
        quantidade_registros=("id", "size"),
        valor_pago_soma_linhas=("valor_pago", "sum"),
        data_pagamento_min=("data_pagamento", "min"),
        data_pagamento_max=("data_pagamento", "max")
    ).reset_index()

    pagamentos["status"] = "consistente"

    pagamentos.loc[
        pagamentos["quantidade_registros"] > 1,
        "status"
    ] = "chave_repetida"

    return pagamentos


def main():
    df = carregar_dados()

    empenhos = consolidar_empenhos(df)
    liquidacoes = consolidar_liquidacoes(df)
    pagamentos = consolidar_pagamentos(df)

    arquivos = {
        "empenhos_consolidados.csv": empenhos,
        "liquidacoes_consolidadas.csv": liquidacoes,
        "pagamentos_consolidados.csv": pagamentos
    }

    for nome, dados in arquivos.items():
        caminho = SAIDA / nome
        dados.to_csv(caminho, index=False)
        print(f"{nome}: {len(dados):,} registros")

    print("\nEmpenhos divergentes:")
    print(
        empenhos["status"].value_counts().to_string()
    )

    print("\nPagamentos:")
    print(
        pagamentos["status"].value_counts().to_string()
    )


if __name__ == "__main__":
    main()
