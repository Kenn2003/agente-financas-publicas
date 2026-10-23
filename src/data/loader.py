import pandas as pd
import json
import requests
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PASTA_DADOS = RAIZ / "data" / "raw" / "csv"

ARQUIVOS = {
    "arrecadacao": "historico_arrecadacao.csv",
    "gastos_diretos": "historico_gastos_diretos.csv",
    "folha_pagamento": "historico_folha_pagamento.csv",
    "receitas_recentes": "atual_receitas.csv"
}
sessao = requests.Session()

def carregar_csvs(pasta_base, arquivos, sep = ","):
    """
    Carrega vários arquivos CSV e retorna um dicionário de DataFrames.

    Parâmetros
    ----------
    pasta_base : str
        Caminho da pasta onde estão os arquivos CSV.

    arquivos : dict
        Dicionário no formato:
        {"nome_dataframe": "arquivo.csv"}

    sep : str
        Separador utilizado nos arquivos CSV.

    Retorno
    -------
    dict
        Dicionário contendo os DataFrames carregados.
    """

    pasta_base = Path(pasta_base)
    dataframes = {}

    for nome, arquivo in arquivos.items():

        caminho = pasta_base / arquivo

        try:
            dataframes[nome] = pd.read_csv(
                caminho,
                sep=sep,
                encoding="utf-8-sig",
                dtype=str,
                low_memory=False
            )

            print(
                f"{nome}: "
                f"{len(dataframes[nome])} linhas carregadas."
            )

        except FileNotFoundError:
            print(f"Arquivo não encontrado: {caminho}")

        except Exception as erro:
            print(f"Erro ao carregar {arquivo}: {erro}")

    return dataframes


def print_colunas(dataframes):
    """
    Exibe as colunas dos DataFrames carregados.
    """

    for nome, df in dataframes.items():

        print(
            f"\n=== Colunas de '{nome}' "
            f"({len(df.columns)} colunas) ==="
        )

        for coluna in df.columns:
            print(f"  • {coluna}")

        print("-" * 50)


def diagnosticar_dados(dataframes):
    """
    Identifica valores ausentes e linhas duplicadas
    em cada DataFrame.
    """

    for nome, df in dataframes.items():

        print(f"\n{'=' * 50}")
        print(f"DIAGNÓSTICO: {nome}")
        print(f"{'=' * 50}")

        print(f"Linhas: {len(df)}")
        print(f"Colunas: {len(df.columns)}")

        # Identifica valores ausentes
        nulos = df.isna().sum()
        nulos = nulos[nulos > 0]

        print("\nColunas com valores ausentes:")
        print(nulos if not nulos.empty else "Nenhuma")

        # Identifica linhas integralmente duplicadas
        duplicados = df.duplicated().sum()

        print(f"\nLinhas duplicadas: {duplicados}")



def analisar_duplicidades(df, nome, chaves):

    print(f"\nANÁLISE DE DUPLICIDADES: {nome}")

    # Registros integralmente duplicados
    duplicados = df.duplicated().sum()

    print("Linhas integralmente duplicadas:", duplicados)

    # Identificadores repetidos
    if "id" in df.columns:

        ids_repetidos = df["id"].duplicated().sum()

        print("IDs repetidos:", ids_repetidos)
        print("IDs distintos:", df["id"].nunique())

    # Repetições conforme a chave de análise
    repeticoes = df.duplicated(subset=chaves).sum()

    print(
        f"Registros repetidos por {chaves}:",
        repeticoes
    )
    

def transformar_dados(dataframes):

    tratados = {}

    for nome, original in dataframes.items():

        df = original.copy()

        # Remove colunas integralmente vazias
        df = df.dropna(axis=1, how="all")

        # Converte valores monetários
        colunas_valores = [
            coluna for coluna in df.columns
            if coluna.startswith("valor_")
            or coluna.startswith("vencimento_")
            or coluna.startswith("desconto_")
            or coluna == "receita_valor"
        ]

        for coluna in colunas_valores:
            df[coluna] = pd.to_numeric(
                df[coluna],
                errors="coerce"
            )

        # Converte campos de data
        colunas_datas = [
            coluna for coluna in df.columns
            if coluna.startswith("data_")
            or coluna == "data"
            or coluna == "receita_data_ocorrencia"
        ]

        for coluna in colunas_datas:
            df[coluna] = pd.to_datetime(
                df[coluna],
                errors="coerce",
                dayfirst=True
            )

        tratados[nome] = df

        print(
            f"{nome}: "
            f"{len(df)} registros, "
            f"{len(df.columns)} colunas tratadas."
        )

    return tratados


def salvar_dados(dataframes):

    destino = RAIZ / "data" / "processed"
    destino.mkdir(parents=True, exist_ok=True)

    for nome, df in dataframes.items():

        caminho = destino / f"{nome}.csv"

        df.to_csv(
            caminho,
            index=False,
            sep=",",
            encoding="utf-8-sig"
        )

        print(f"Arquivo salvo: {caminho}")

if __name__ == "__main__":

    dataframes = carregar_csvs(
        PASTA_DADOS,
        ARQUIVOS
    )

    tratados = transformar_dados(dataframes)

    salvar_dados(tratados)


# df = dataframes["gastos_diretos"].copy()

# chaves = [
#     "ano_referencia",
#     "cod_unidade",
#     "empenho"
# ]

# repetidos = df[
#     df.duplicated(subset=chaves, keep=False)
# ].copy()

# analise = (
#     repetidos
#     .groupby(chaves, dropna=False)
#     .agg(
#         quantidade_registros=("id", "size"),
#         valores_empenho_distintos=("valor_empenho", "nunique"),
#         liquidacoes_distintas=("liquidacao", "nunique"),
#         pagamentos_distintos=("numero_pagamento", "nunique")
#     )
#     .reset_index()
# )

# print("\nEMPENHOS REPETIDOS")
# print("Quantidade de grupos:", len(analise))

# print("\nGrupos com diferentes valores de empenho:")
# print((analise["valores_empenho_distintos"] > 1).sum())

# print("\nGrupos com diferentes liquidações:")
# print((analise["liquidacoes_distintas"] > 1).sum())

# print("\nGrupos com diferentes pagamentos:")
# print((analise["pagamentos_distintos"] > 1).sum())

# print("\nExemplos:")
# print(analise.head(10).to_string(index=False))

# divergencias = analise[
#     analise["valores_empenho_distintos"] > 1
# ]


# registros_divergentes = df.merge(
#     divergencias[chaves],
#     on=chaves,
#     how="inner"
# )

# colunas = [
#     "id",
#     "ano_referencia",
#     "cod_unidade",
#     "empenho",
#     "liquidacao",
#     "numero_pagamento",
#     "valor_empenho",
#     "valor_liq",
#     "valor_pago"
# ]

# print("\nREGISTROS COM DIVERGÊNCIA:")
# print(
#     registros_divergentes[colunas]
#     .to_string(index=False)
# )

