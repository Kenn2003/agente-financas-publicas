import geopandas as gpd
import pandas as pd
import numpy as np

from pathlib import Path

RAIZ = Path(r"C:\Users\kennk\agente-financas-publicas")
PASTA = RAIZ / "data" / "processed"

CRS_METRICO = "EPSG:31982"


# ==================================================
# 1. CARREGAMENTO DAS BASES
# ==================================================

areas = gpd.read_file(
    PASTA / "palmas_areas_consolidadas.gpkg",
    layer="areas_consolidadas"
)

setores = gpd.read_file(
    PASTA / "palmas_setores_socioeconomicos_2022.gpkg",
    layer="setores_palmas"
)

censo = pd.read_csv(
    PASTA / "base_censitaria_palmas_2022.csv",
    sep=";",
    encoding="utf-8-sig",
    dtype={"codigo_setor": str}
)

areas = areas.to_crs(CRS_METRICO)
setores = setores.to_crs(CRS_METRICO)

setores["codigo_setor"] = (
    setores["codigo_setor"]
    .astype(str)
    .str.strip()
)

censo["codigo_setor"] = (
    censo["codigo_setor"]
    .str.strip()
)

assert areas["id_area"].is_unique
assert setores["codigo_setor"].is_unique
assert censo["codigo_setor"].is_unique

assert areas.is_valid.all()
assert setores.is_valid.all()

print("Áreas municipais:", len(areas))
print("Setores censitários:", len(setores))


# ==================================================
# 2. INTEGRAÇÃO DOS ATRIBUTOS CENSITÁRIOS
# ==================================================

setores = setores[
    ["codigo_setor", "geometry"]
].merge(
    censo[
        [
            "codigo_setor",
            "populacao_total",
            "responsaveis",
            "moradores",
            "renda_media_responsavel",
            "renda_mediana_responsavel"
        ]
    ],
    on="codigo_setor",
    how="left",
    validate="one_to_one",
    indicator=True
)

assert setores["_merge"].eq("both").all()

setores = setores.drop(columns="_merge")


# ==================================================
# 3. ÁREAS ORIGINAIS
# ==================================================

areas["area_municipal_m2"] = (
    areas.geometry.area
)

setores["area_setor_m2"] = (
    setores.geometry.area
)

assert areas["area_municipal_m2"].gt(0).all()
assert setores["area_setor_m2"].gt(0).all()


# ==================================================
# 4. INTERSEÇÃO ESPACIAL
# ==================================================

print("\nExecutando interseção espacial...")

intersecoes = gpd.overlay(
    areas[
        [
            "id_area",
            "nome_area",
            "regiao_geopalmas",
            "divergencia_nomes",
            "area_municipal_m2",
            "geometry"
        ]
    ],
    setores,
    how="intersection",
    keep_geom_type=True,
    make_valid=False
)

intersecoes["area_intersecao_m2"] = (
    intersecoes.geometry.area
)

intersecoes = intersecoes[
    intersecoes["area_intersecao_m2"] > 0
].copy()


# ==================================================
# 5. COEFICIENTES ESPACIAIS
# ==================================================

intersecoes["fracao_setor"] = (
    intersecoes["area_intersecao_m2"]
    / intersecoes["area_setor_m2"]
)

intersecoes["fracao_area_municipal"] = (
    intersecoes["area_intersecao_m2"]
    / intersecoes["area_municipal_m2"]
)

intersecoes["percentual_setor"] = (
    intersecoes["fracao_setor"] * 100
)

intersecoes["percentual_area_municipal"] = (
    intersecoes["fracao_area_municipal"] * 100
)

TOLERANCIA = 1e-8

assert intersecoes["fracao_setor"].between(
    0, 1 + TOLERANCIA
).all()

assert intersecoes["fracao_area_municipal"].between(
    0, 1 + TOLERANCIA
).all()


# ==================================================
# 6. DIAGNÓSTICO DE COBERTURA
# ==================================================

cobertura = (
    intersecoes
    .groupby("id_area")
    .agg(
        setores_interceptados=(
            "codigo_setor", "nunique"
        ),
        area_interceptada_m2=(
            "area_intersecao_m2", "sum"
        ),
        fracao_cobertura=(
            "fracao_area_municipal", "sum"
        )
    )
    .reset_index()
)

cobertura = areas[
    [
        "id_area",
        "nome_area",
        "regiao_geopalmas",
        "area_municipal_m2"
    ]
].merge(
    cobertura,
    on="id_area",
    how="left",
    validate="one_to_one"
)

colunas_zero = [
    "setores_interceptados",
    "area_interceptada_m2",
    "fracao_cobertura"
]

cobertura[colunas_zero] = (
    cobertura[colunas_zero].fillna(0)
)

cobertura["percentual_cobertura"] = (
    cobertura["fracao_cobertura"] * 100
)

cobertura["area_nao_coberta_m2"] = (
    cobertura["area_municipal_m2"]
    - cobertura["area_interceptada_m2"]
)


# ==================================================
# 7. CONTROLE DE SOBREPOSIÇÕES RESIDUAIS
# ==================================================

controle_setores = (
    intersecoes
    .groupby("codigo_setor")
    .agg(
        areas_interceptadas=("id_area", "nunique"),
        soma_fracoes=("fracao_setor", "sum")
    )
    .reset_index()
)

excesso = controle_setores[
    controle_setores["soma_fracoes"] > 1 + TOLERANCIA
]


# ==================================================
# 8. EXPORTAÇÃO
# ==================================================

intersecoes.to_file(
    PASTA / "intersecoes_geopalmas_ibge.gpkg",
    layer="intersecoes",
    driver="GPKG"
)

intersecoes.drop(
    columns="geometry"
).to_csv(
    PASTA / "correspondencia_areas_setores.csv",
    sep=";",
    encoding="utf-8-sig",
    index=False
)

cobertura.to_csv(
    PASTA / "cobertura_censitaria_areas.csv",
    sep=";",
    encoding="utf-8-sig",
    index=False
)

controle_setores.to_csv(
    PASTA / "controle_intersecoes_setores.csv",
    sep=";",
    encoding="utf-8-sig",
    index=False
)


# ==================================================
# 9. RELATÓRIO FINAL
# ==================================================

print("\n" + "=" * 60)
print("INTEGRAÇÃO GEOPALMAS x IBGE")

print("\nÁreas municipais:", len(areas))
print("Setores originais:", len(setores))
print("Fragmentos de interseção:", len(intersecoes))

print("\nÁreas municipais interceptadas:",
      intersecoes["id_area"].nunique())

print("Setores censitários interceptados:",
      intersecoes["codigo_setor"].nunique())

print("\nGeometrias inválidas:",
      (~intersecoes.is_valid).sum())

print("\nESTATÍSTICAS DE COBERTURA:")

print(
    cobertura["percentual_cobertura"].describe()
)

print("\nSETORES POR ÁREA MUNICIPAL:")

print(
    cobertura["setores_interceptados"].describe()
)

print("\nÁREAS COM COBERTURA INFERIOR A 99%:")

print(
    cobertura.loc[
        cobertura["percentual_cobertura"] < 99,
        [
            "nome_area",
            "regiao_geopalmas",
            "percentual_cobertura"
        ]
    ].to_string(index=False)
)

print("\nÁREAS COM COBERTURA SUPERIOR A 100,01%:")

print(
    cobertura.loc[
        cobertura["percentual_cobertura"] > 100.01,
        ["nome_area", "percentual_cobertura"]
    ].to_string(index=False)
)

print("\nSETORES COM SOMA DAS FRAÇÕES SUPERIOR A 1:")

print(excesso.to_string(index=False))

print("\nAMOSTRA DAS INTERSEÇÕES:")

print(
    intersecoes[
        [
            "nome_area",
            "codigo_setor",
            "percentual_setor",
            "percentual_area_municipal"
        ]
    ].head(20).to_string(index=False)
)

print("\nArquivos exportados com sucesso.")
