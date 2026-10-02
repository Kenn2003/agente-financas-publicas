import pandas as pd
from pathlib import Path

PASTA_DADOS = "C:/Users/kennk/agente-financas-publicas"

ARQUIVOS = {
    "contratos": "contratos.csv",
    "despesas": "despesas.csv",
    "receita_acessoinformacao": "receita_acessoinformacao.csv",
    "receita_palmas": "receita_palmas.csv",
    "servidores": "servidores.csv",
    "licitacoes": "licitacoes.csv",
    "folha_palmas": "folha_palmas.csv",
    "pagamentos_palmas": "pagamentos_palmas.csv",
    "divida_ativa": "relatorio_dívida_ativa.csv",
    "relatorio_licitacoes": "relatorio_licitacoes.csv",
    "sancoes_administrativas": "relatorio_sanções_administrativas.csv"
}

def carregar_csvs(pasta_base, arquivos, sep=";"):
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


dataframes = carregar_csvs(
    PASTA_DADOS,
    ARQUIVOS
)


print_colunas(dataframes)