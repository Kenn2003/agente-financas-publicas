from pathlib import Path

import pandas as pd


DATA_DIRECTORY = Path("data/ready")

ARQUIVOS = [
    "arrecadacao.parquet",
    "folha_pagamento.parquet",
    "gastos_diretos.parquet",
    "receitas_recentes.parquet",
]


def analisar_arquivo(caminho: Path) -> None:
    """Analisa um arquivo Parquet preparado pelo ETL."""

    if not caminho.exists():
        print(f"\nArquivo não encontrado: {caminho}")
        return

    dataframe = pd.read_parquet(caminho)

    print("\n" + "=" * 90)
    print(f"ARQUIVO: {caminho}")
    print("=" * 90)

    print(f"Quantidade de registros: {len(dataframe)}")
    print(f"Quantidade de colunas: {len(dataframe.columns)}")

    print("\nColunas e tipos:")
    for coluna in dataframe.columns:
        print(f"- {coluna}: {dataframe[coluna].dtype}")

    print("\nValores nulos por coluna:")
    print(dataframe.isna().sum().to_string())

    print("\nRegistros totalmente duplicados:")
    print(dataframe.duplicated().sum())

    print("\nAmostra dos dados:")
    print(dataframe.head(3).to_string())

    print("\nResumo estatístico:")
    print(dataframe.describe(include="all").transpose().to_string())


def main() -> None:
    for nome_arquivo in ARQUIVOS:
        caminho = DATA_DIRECTORY / nome_arquivo

        try:
            analisar_arquivo(caminho)
        except Exception as erro:
            print(f"\nErro ao analisar {caminho}: {erro}")


if __name__ == "__main__":
    main()