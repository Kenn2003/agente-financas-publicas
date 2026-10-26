from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import requests


# Código oficial de Palmas/TO no IBGE
CODIGO_PALMAS = "1721000"


# Censo Demográfico 2022
# Agregados por bairros - arquivo básico
URL_POPULACAO = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
    "Agregados_por_Setores_Censitarios/Agregados_por_Bairro_csv/"
    "Agregados_por_bairros_basico_BR_20260520.zip"
)


# Censo Demográfico 2022
# Rendimento do responsável por bairro
URL_RENDA = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
    "Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/"
    "Agregados_por_bairros_renda_responsavel_BR_20260508_csv.zip"
)


def ler_zip_ibge(url):
    """
    Baixa um arquivo ZIP oficial do IBGE
    e retorna o CSV como DataFrame.
    """

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
                encoding="utf-8",
                low_memory=False
            )

    dados.columns = (
        dados.columns
        .str.strip()
        .str.upper()
    )

    return dados


def filtrar_palmas(dados):
    """
    Retorna somente registros do município
    de Palmas/TO.
    """

    palmas = dados[
        dados["CD_MUN"].astype(str) == CODIGO_PALMAS
    ].copy()

    if palmas.empty:
        raise ValueError(
            "Nenhum dado de Palmas/TO foi encontrado no arquivo do IBGE."
        )

    return palmas


def obter_enriquecimento_ibge():
    """
    Retorna população e rendimento médio
    dos bairros de Palmas/TO utilizando
    dados do Censo Demográfico 2022.
    """

    # ==========================
    # POPULAÇÃO DOS BAIRROS
    # ==========================

    populacao = ler_zip_ibge(URL_POPULACAO)

    # Recorte territorial: somente Palmas
    populacao = filtrar_palmas(populacao)

    populacao = populacao[
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

    populacao["populacao"] = pd.to_numeric(
        populacao["populacao"],
        errors="coerce"
    )


    # ==========================
    # RENDIMENTO DOS BAIRROS
    # ==========================

    renda = ler_zip_ibge(URL_RENDA)

    # Recorte territorial: somente Palmas
    renda = filtrar_palmas(renda)

    renda = renda[
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

    renda["rendimento_medio"] = pd.to_numeric(
        renda["rendimento_medio"],
        errors="coerce"
    )


    # ==========================
    # JUNÇÃO PELO BAIRRO
    # ==========================

    resultado = populacao.merge(
        renda,
        on="CD_BAIRRO",
        how="left"
    )


    resultado = resultado.rename(
        columns={
            "CD_BAIRRO": "codigo_bairro_ibge",
            "NM_BAIRRO": "bairro"
        }
    )


    resultado["municipio"] = "Palmas"
    resultado["uf"] = "TO"
    resultado["ano_censo"] = 2022
    resultado["fonte"] = "IBGE - Censo Demográfico 2022"


    resultado = resultado[
        [
            "codigo_bairro_ibge",
            "bairro",
            "municipio",
            "uf",
            "ano_censo",
            "populacao",
            "rendimento_medio",
            "fonte"
        ]
    ]


    # Um registro por bairro
    resultado = (
        resultado
        .drop_duplicates(subset=["codigo_bairro_ibge"])
        .sort_values("bairro")
        .reset_index(drop=True)
    )

    return resultado


def listar_bairros_palmas():
    """
    Retorna somente os bairros oficiais
    de Palmas encontrados no Censo 2022.
    """

    dados = obter_enriquecimento_ibge()

    return dados[
        [
            "codigo_bairro_ibge",
            "bairro"
        ]
    ]


if __name__ == "__main__":

    dados = obter_enriquecimento_ibge()

    print("\nBAIRROS DE PALMAS - CENSO 2022\n")

    print(
        dados.to_string(index=False)
    )

    print(
        f"\nTotal de bairros encontrados: {len(dados)}"
    )
