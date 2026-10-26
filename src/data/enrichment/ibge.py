from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import requests


# Código oficial de Palmas/TO no IBGE
CODIGO_PALMAS = "1721000"

# Censo 2022 - dados básicos por bairro
URL_POPULACAO = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
    "Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/"
    "Agregados_por_bairros_basico_BR_20260520.zip"
)

# Censo 2022 - rendimento do responsável por bairro
URL_RENDA = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
    "Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/"
    "Agregados_por_bairros_renda_responsavel_BR_20260508_csv.zip"
)


def ler_zip_ibge(url):
    """Baixa um ZIP do IBGE e lê o CSV existente dentro dele."""

    resposta = requests.get(url, timeout=60)
    resposta.raise_for_status()

    with ZipFile(BytesIO(resposta.content)) as arquivo_zip:

        nome_csv = next(
            nome
            for nome in arquivo_zip.namelist()
            if nome.lower().endswith(".csv")
        )

        with arquivo_zip.open(nome_csv) as arquivo_csv:

            dados = pd.read_csv(
                arquivo_csv,
                sep=";",
                dtype=str,
                encoding="latin-1",
                low_memory=False
            )

    # Padroniza os nomes das colunas
    dados.columns = dados.columns.str.strip().str.upper()

    return dados


def obter_enriquecimento_ibge():
    """
    Retorna população e rendimento médio
    dos bairros de Palmas/TO.
    """

    # -------------------------
    # POPULAÇÃO
    # V0001 = total de pessoas
    # -------------------------

    populacao = ler_zip_ibge(URL_POPULACAO)

    populacao = populacao[
        populacao["CD_MUN"] == CODIGO_PALMAS
    ][
        [
            "CD_BAIRRO",
            "NM_BAIRRO",
            "V0001"
        ]
    ].copy()

    populacao = populacao.rename(
        columns={
            "V0001": "populacao"
        }
    )


    # -------------------------
    # RENDIMENTO
    # V06004 - verificar definição no dicionário do IBGE
    # -------------------------
    
    renda = ler_zip_ibge(URL_RENDA)
    
    # Seleciona apenas os bairros presentes
    # na tabela de população de Palmas
    codigos_palmas = populacao["CD_BAIRRO"].unique()
    
    renda = renda[
        renda["CD_BAIRRO"].isin(codigos_palmas)
    ][
        [
            "CD_BAIRRO",
            "V06004"
        ]
    ].copy()
    
    renda = renda.rename(
        columns={
            "V06004": "rendimento_medio"
        }
    )


    # Junta população e renda
    # utilizando o código oficial do bairro
    resultado = populacao.merge(
        renda,
        on="CD_BAIRRO",
        how="left"
    )


    # Nomes mais claros para o ETL
    resultado = resultado.rename(
        columns={
            "CD_BAIRRO": "codigo_bairro_ibge",
            "NM_BAIRRO": "bairro"
        }
    )

    resultado["municipio"] = "Palmas"
    resultado["uf"] = "TO"
    resultado["fonte"] = "IBGE - Censo Demográfico 2022"


    return resultado[
        [
            "codigo_bairro_ibge",
            "bairro",
            "municipio",
            "uf",
            "populacao",
            "rendimento_medio",
            "fonte"
        ]
    ]


if __name__ == "__main__":

    dados = obter_enriquecimento_ibge()

    print(dados.to_string(index=False))

    print(
        f"\nTotal de bairros encontrados: {len(dados)}"
    )
