from pathlib import Path

import pandas as pd


PASTAS_DE_DADOS = [
    Path("data/pronto"),
    Path("data/limpo"),
    Path("data/bruto"),
    Path("data"),
]


def carregar_arquivo(caminho: Path) -> pd.DataFrame:
    """Carrega arquivos de dados em um DataFrame."""

    extensao = caminho.suffix.lower()

    if extensao == ".csv":
        for encoding in ["utf-8", "latin1", "cp1252"]:
            try:
                return pd.read_csv(caminho, encoding=encoding)
            except UnicodeDecodeError:
                continue

        raise ValueError(
            f"Não foi possível identificar o encoding de {caminho}"
        )

    if extensao == ".json":
        return pd.read_json(caminho)

    if extensao == ".parquet":
        return pd.read_parquet(caminho)

    if extensao in {".xlsx", ".xls"}:
        return pd.read_excel(caminho)

    raise ValueError(f"Formato não suportado: {caminho}")


def analisar_arquivo(caminho: Path) -> None:
    """Exibe informações básicas sobre um arquivo de dados."""

    dataframe = carregar_arquivo(caminho)

    print("\n" + "=" * 80)
    print(f"ARQUIVO: {caminho}")
    print("=" * 80)

    print(f"Quantidade de registros: {len(dataframe)}")
    print(f"Quantidade de colunas: {len(dataframe.columns)}")

    print("\nColunas:")
    for coluna in dataframe.columns:
        print(f"- {coluna}")

    print("\nTipos de dados:")
    print(dataframe.dtypes)

    print("\nValores nulos:")
    print(dataframe.isna().sum())

    print("\nRegistros duplicados:")
    print(dataframe.duplicated().sum())

    print("\nPrimeiros registros:")
    print(dataframe.head(3).to_string())


def encontrar_arquivos() -> list[Path]:
    """Procura arquivos de dados nas pastas do projeto."""

    extensoes_permitidas = {
        ".csv",
        ".json",
        ".parquet",
        ".xlsx",
        ".xls",
    }

    arquivos_encontrados = []

    for pasta in PASTAS_DE_DADOS:
        if not pasta.exists():
            continue

        for arquivo in pasta.rglob("*"):
            if (
                arquivo.is_file()
                and arquivo.suffix.lower() in extensoes_permitidas
            ):
                if arquivo not in arquivos_encontrados:
                    arquivos_encontrados.append(arquivo)

    return arquivos_encontrados


def main() -> None:
    arquivos = encontrar_arquivos()

    if not arquivos:
        print("Nenhum arquivo de dados foi encontrado.")
        print()
        print("Foram procurados arquivos nas pastas:")
        for pasta in PASTAS_DE_DADOS:
            print(f"- {pasta}")

        print()
        print(
            "Isso significa que os dados ainda não foram baixados "
            "ou estão em outro formato/local."
        )
        return

    print(f"Foram encontrados {len(arquivos)} arquivo(s).")

    for arquivo in arquivos:
        try:
            analisar_arquivo(arquivo)
        except Exception as erro:
            print(f"\nErro ao analisar {arquivo}: {erro}")


if __name__ == "__main__":
    main()