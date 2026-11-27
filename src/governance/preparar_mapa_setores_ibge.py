"""Prepara os mapas temáticos por setor censitário de Palmas (Censo 2022).

Entradas públicas em data/raw/ibge_2022:
- TO_setores_CD2022.gpkg (geometria IBGE, EPSG:4674)
- Agregados_por_setores_basico_BR_20260520.zip (população V0001)
- Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip (V06004/V06006)

Gera GeoPackage métrico e GeoJSON para a página Dash. A renda continua agregada
ao setor; não representa renda de indivíduos ou renda domiciliar per capita.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "ibge_2022"
OUT = ROOT / "data" / "processed" / "ibge_palmas_2022"
MUNICIPIO = "1721000"
CRS_AREA = "EPSG:31982"
CRS_WEB = "EPSG:4326"

ARQUIVO_GEOMETRIA = RAW / "TO_setores_CD2022.gpkg"
ARQUIVO_BASICO = RAW / "Agregados_por_setores_basico_BR_20260520.zip"
ARQUIVO_RENDA = RAW / "Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip"


def _ler_tabela_zip(caminho: Path) -> pd.DataFrame:
    with ZipFile(caminho) as pacote:
        csvs = [nome for nome in pacote.namelist() if nome.lower().endswith(".csv")]
        if len(csvs) != 1:
            raise ValueError(f"Esperado um CSV em {caminho.name}; encontrados {len(csvs)}")
        with pacote.open(csvs[0]) as arquivo:
            tabela = pd.read_csv(
                arquivo, sep=";", dtype=str, encoding="latin-1", low_memory=False
            )
    tabela.columns = tabela.columns.str.strip().str.upper()
    return tabela


def _numero(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.astype("string").str.strip(), errors="coerce")


def preparar() -> dict[str, int | float | str]:
    for caminho in (ARQUIVO_GEOMETRIA, ARQUIVO_BASICO, ARQUIVO_RENDA):
        if not caminho.is_file():
            raise FileNotFoundError(f"Insumo oficial não encontrado: {caminho}")

    geometria = gpd.read_file(
        ARQUIVO_GEOMETRIA,
        layer="TO_setores_CD2022",
        columns=["CD_SETOR", "CD_MUN", "NM_MUN", "NM_DIST", "NM_BAIRRO"],
    )
    if geometria.crs is None or geometria.crs.to_epsg() != 4674:
        raise ValueError(f"CRS inesperado na malha IBGE: {geometria.crs}")
    geometria["CD_SETOR"] = geometria["CD_SETOR"].astype("string").str.strip()
    geometria["CD_MUN"] = geometria["CD_MUN"].astype("string").str.strip().str.zfill(7)
    geometria = geometria.loc[geometria["CD_MUN"].eq(MUNICIPIO)].copy()
    if geometria.empty:
        raise ValueError("A malha IBGE não contém setores do município 1721000.")

    # Um setor tem duas partes na malha; dissolve a geometria sem somar os atributos.
    geometrias_por_setor = geometria.dissolve(
        by="CD_SETOR", as_index=False, aggfunc="first"
    )
    if geometrias_por_setor["CD_SETOR"].duplicated().any():
        raise ValueError("A malha ainda tem códigos de setor duplicados após dissolução.")

    basico = _ler_tabela_zip(ARQUIVO_BASICO)
    obrigatorias = {"CD_SETOR", "CD_MUN", "V0001"}
    if not obrigatorias.issubset(basico.columns):
        raise ValueError(f"Colunas ausentes na tabela básica: {obrigatorias - set(basico.columns)}")
    basico["CD_MUN"] = basico["CD_MUN"].astype("string").str.strip().str.zfill(7)
    basico["CD_SETOR"] = basico["CD_SETOR"].astype("string").str.strip()
    basico = basico.loc[basico["CD_MUN"].eq(MUNICIPIO), ["CD_SETOR", "V0001"]].copy()
    basico["V0001"] = _numero(basico["V0001"])
    if basico["CD_SETOR"].duplicated().any():
        raise ValueError("Tabela básica tem mais de uma linha para algum setor de Palmas.")

    renda = _ler_tabela_zip(ARQUIVO_RENDA)
    obrigatorias = {"CD_SETOR", "V06004", "V06006"}
    if not obrigatorias.issubset(renda.columns):
        raise ValueError(f"Colunas ausentes na tabela de renda: {obrigatorias - set(renda.columns)}")
    renda["CD_SETOR"] = renda["CD_SETOR"].astype("string").str.strip()
    renda = renda.loc[
        renda["CD_SETOR"].str.startswith(MUNICIPIO),
        ["CD_SETOR", "V06004", "V06006"],
    ].copy()
    renda["V06004"] = _numero(renda["V06004"])
    renda["V06006"] = _numero(renda["V06006"])
    if renda["CD_SETOR"].duplicated().any():
        raise ValueError("Tabela de renda tem mais de uma linha para algum setor de Palmas.")

    codigos_geo = set(geometrias_por_setor["CD_SETOR"])
    codigos_pop = set(basico["CD_SETOR"])
    if codigos_geo != codigos_pop:
        raise ValueError(
            "A geometria e a tabela básica não cobrem os mesmos setores. "
            f"Sem população: {len(codigos_geo - codigos_pop)}; sem geometria: {len(codigos_pop - codigos_geo)}."
        )
    if not set(renda["CD_SETOR"]).issubset(codigos_geo):
        raise ValueError("A tabela de renda contém setores sem geometria municipal correspondente.")

    gdf = geometrias_por_setor.merge(
        basico, on="CD_SETOR", how="left", validate="one_to_one"
    ).merge(renda, on="CD_SETOR", how="left", validate="one_to_one")
    if gdf["V0001"].isna().any():
        raise ValueError("Há setores sem população após o vínculo por CD_SETOR.")
    if not gdf.geometry.is_valid.all():
        raise ValueError("A malha IBGE contém geometrias inválidas após dissolução.")

    metrico = gdf.to_crs(CRS_AREA)
    metrico["area_km2"] = metrico.geometry.area / 1_000_000
    if metrico["area_km2"].le(0).any():
        raise ValueError("A malha contém setores sem área positiva.")
    metrico["densidade_demografica"] = metrico["V0001"] / metrico["area_km2"]
    metrico["renda_disponivel"] = metrico["V06006"].notna()

    def suporte(linha):
        if not linha["renda_disponivel"]:
            return "Indisponível"
        if linha["V0001"] >= 100:
            return "Alto"
        if linha["V0001"] >= 30:
            return "Moderado"
        return "Baixo"

    metrico["suporte_analitico"] = metrico.apply(suporte, axis=1)

    OUT.mkdir(parents=True, exist_ok=True)
    gpkg = OUT / "setores_palmas_2022.gpkg"
    geojson = OUT / "setores_palmas_2022.geojson"
    web = metrico.to_crs(CRS_WEB)
    if gpkg.exists():
        gpkg.unlink()
    metrico.to_file(gpkg, layer="setores_palmas_2022", driver="GPKG")
    web.to_file(geojson, driver="GeoJSON", index=False)

    resumo = {
        "data_preparacao": date.today().isoformat(),
        "municipio_codigo_ibge": MUNICIPIO,
        "municipio": "Palmas/TO",
        "ano_referencia": 2022,
        "setores": int(len(metrico)),
        "populacao_total": int(metrico["V0001"].sum()),
        "setores_com_renda_mediana": int(metrico["V06006"].notna().sum()),
        "setores_sem_renda_mediana": int(metrico["V06006"].isna().sum()),
        "setores_com_renda_media": int(metrico["V06004"].notna().sum()),
        "setores_com_geometria_dissolvida": int(len(geometria) - len(geometrias_por_setor)),
        "crs_origem": "EPSG:4674",
        "crs_area": CRS_AREA,
        "crs_geojson": CRS_WEB,
        "campo_rendimento_mediano": "V06006",
        "descricao_rendimento": "Rendimento nominal mensal mediano das pessoas responsáveis com rendimento em domicílios particulares permanentes ocupados; R$ nominais de 2022.",
        "campo_rendimento_medio": "V06004",
        "campo_populacao": "V0001",
        "metodo_densidade": "População V0001 dividida pela área geométrica do setor calculada em EPSG:31982.",
        "metodo_suporte": "Exploratório por setor: indisponível sem V06006; baixo se população <30; moderado se >=30; alto se >=100. Não é medida de incerteza estatística.",
        "fonte_geometria": "IBGE, Malha de Setores Censitários 2022, Tocantins.",
        "fonte_populacao": "IBGE, Agregados por Setores Censitários, Básico, arquivo 20260520.",
        "fonte_rendimento": "IBGE, Agregados por Setores Censitários, Rendimento do Responsável, arquivo 20260508.",
        "arquivo_geopackage": str(gpkg.relative_to(ROOT)),
        "arquivo_geojson": str(geojson.relative_to(ROOT)),
    }
    (OUT / "metadados.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return resumo


if __name__ == "__main__":
    print(json.dumps(preparar(), ensure_ascii=False, indent=2))
