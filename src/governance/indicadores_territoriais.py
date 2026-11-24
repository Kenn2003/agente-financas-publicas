import pandas as pd
import geopandas as gpd
import numpy as np

from pathlib import Path

RAIZ = Path(r"C:\Users\kennk\agente-financas-publicas")
PASTA = RAIZ / "data" / "processed"


# ==================================================
# 1. CARREGAMENTO
# ==================================================

df = pd.read_csv(
    PASTA / "correspondencia_areas_setores.csv",
    sep=";",
    encoding="utf-8-sig",
    dtype={"codigo_setor": str}
)

areas = gpd.read_file(
    PASTA / "palmas_areas_consolidadas.gpkg",
    layer="areas_consolidadas"
)

censo = pd.read_csv(
    PASTA / "base_censitaria_palmas_2022.csv",
    sep=";",
    encoding="utf-8-sig",
    dtype={"codigo_setor": str}
)

print("Fragmentos:", len(df))
print("Áreas municipais:", len(areas))


# ==================================================
# 2. NORMALIZAÇÃO DAS FRAÇÕES
# ==================================================

df["soma_fracoes_setor"] = (
    df.groupby("codigo_setor")["fracao_setor"]
    .transform("sum")
)

df["fator_correcao"] = (
    df["soma_fracoes_setor"].clip(lower=1)
)

df["fracao_setor_ajustada"] = (
    df["fracao_setor"]
    / df["fator_correcao"]
)

controle = (
    df.groupby("codigo_setor")
    ["fracao_setor_ajustada"].sum()
)

assert controle.le(1 + 1e-8).all()


# ==================================================
# 3. ESTIMATIVAS DEMOGRÁFICAS
# ==================================================

df["populacao_estimada"] = (
    df["populacao_total"]
    * df["fracao_setor_ajustada"]
)

df["responsaveis_estimados"] = (
    df["responsaveis"]
    * df["fracao_setor_ajustada"]
)

df["moradores_estimados"] = (
    df["moradores"]
    * df["fracao_setor_ajustada"]
)


# ==================================================
# 4. DISPONIBILIDADE DOS DADOS DE RENDA
# ==================================================

df["possui_renda"] = (
    df["renda_media_responsavel"].notna()
    & df["renda_mediana_responsavel"].notna()
)

df["area_com_renda_m2"] = (
    df["area_intersecao_m2"]
    .where(df["possui_renda"], 0)
)

df["populacao_com_renda_estimada"] = (
    df["populacao_estimada"]
    .where(df["possui_renda"], 0)
)


# ==================================================
# 5. PONDERAÇÃO DOS INDICADORES DE RENDA
# ==================================================

def media_ponderada(valores, pesos):

    validos = (
        valores.notna()
        & pesos.notna()
        & pesos.gt(0)
    )

    if not validos.any():
        return np.nan

    return np.average(
        valores[validos],
        weights=pesos[validos]
    )


def soma_preservando_ausentes(serie):
    return serie.sum(min_count=1)


# ==================================================
# 6. AGREGAÇÃO POR ÁREA MUNICIPAL
# ==================================================

registros = []

for id_area, grupo in df.groupby("id_area"):

    area_m2 = grupo["area_municipal_m2"].iloc[0]

    populacao = soma_preservando_ausentes(
        grupo["populacao_estimada"]
    )

    responsaveis = soma_preservando_ausentes(
        grupo["responsaveis_estimados"]
    )

    moradores = soma_preservando_ausentes(
        grupo["moradores_estimados"]
    )

    renda_media = media_ponderada(
        grupo["renda_media_responsavel"],
        grupo["responsaveis_estimados"]
    )

    renda_mediana = media_ponderada(
        grupo["renda_mediana_responsavel"],
        grupo["responsaveis_estimados"]
    )

    cobertura_territorial = (
        grupo["area_com_renda_m2"].sum()
        / area_m2 * 100
    )

    cobertura_populacional = (
        grupo["populacao_com_renda_estimada"].sum()
        / populacao * 100
        if pd.notna(populacao) and populacao > 0
        else np.nan
    )

    registros.append({
        "id_area": id_area,

        "setores_interceptados":
            grupo["codigo_setor"].nunique(),

        "setores_com_renda":
            grupo.loc[
                grupo["possui_renda"],
                "codigo_setor"
            ].nunique(),

        "populacao_estimada": populacao,

        "responsaveis_estimados": responsaveis,

        "moradores_estimados": moradores,

        "densidade_demografica_estimada":
            populacao / (area_m2 / 1e6),

        "indicador_renda_media":
            renda_media,

        "indicador_renda_mediana":
            renda_mediana,

        "cobertura_territorial_renda_pct":
            cobertura_territorial,

        "cobertura_populacional_renda_pct":
            cobertura_populacional,

        "cobertura_responsaveis_area_pct":
            grupo.loc[
                grupo["responsaveis"].notna(),
                "area_intersecao_m2"
            ].sum() / area_m2 * 100,

        "ano_referencia_censo": 2022
    })

indicadores = pd.DataFrame(registros)


# ==================================================
# 7. INTEGRAÇÃO COM A MALHA MUNICIPAL
# ==================================================

gdf = areas.merge(
    indicadores,
    on="id_area",
    how="left",
    validate="one_to_one"
)

assert len(gdf) == len(areas)
assert gdf["id_area"].is_unique
assert gdf.is_valid.all()

gdf["possui_indicador_renda"] = (
    gdf["indicador_renda_mediana"].notna()
)

gdf["populacao_estimada_zero"] = (
    gdf["populacao_estimada"].eq(0)
)


# ==================================================
# 8. CONTROLE POPULACIONAL
# ==================================================

populacao_censo = censo["populacao_total"].sum()

populacao_estimada = (
    gdf["populacao_estimada"].sum()
)

assert populacao_estimada <= populacao_censo + 1e-6

percentual_populacao = (
    populacao_estimada
    / populacao_censo * 100
)


# ==================================================
# 9. EXPORTAÇÃO
# ==================================================

gdf.to_file(
    PASTA / "palmas_areas_socioeconomicas_2022.gpkg",
    layer="areas_socioeconomicas",
    driver="GPKG"
)

gdf.drop(columns="geometry").to_csv(
    PASTA / "indicadores_territoriais_palmas_2022.csv",
    sep=";",
    encoding="utf-8-sig",
    index=False
)

df.to_csv(
    PASTA / "fragmentos_socioeconomicos_palmas.csv",
    sep=";",
    encoding="utf-8-sig",
    index=False
)


# ==================================================
# 10. RELATÓRIO
# ==================================================

print("\n" + "=" * 60)
print("INDICADORES SOCIOECONÔMICOS TERRITORIAIS")

print("\nÁreas municipais:", len(gdf))

print("Áreas com indicador de renda:",
      gdf["possui_indicador_renda"].sum())

print("Áreas sem indicador de renda:",
      (~gdf["possui_indicador_renda"]).sum())

print("Áreas com população estimada zero:",
      gdf["populacao_estimada_zero"].sum())

print("\nPOPULAÇÃO:")

print("População oficial do município:",
      populacao_censo)

print("População estimada nas áreas municipais:",
      round(populacao_estimada, 2))

print("Percentual da população municipal:",
      round(percentual_populacao, 2))

print("\nESTATÍSTICAS DOS INDICADORES:")

print(
    gdf[
        [
            "populacao_estimada",
            "densidade_demografica_estimada",
            "indicador_renda_media",
            "indicador_renda_mediana",
            "cobertura_territorial_renda_pct",
            "cobertura_populacional_renda_pct"
        ]
    ].describe().T.to_string()
)

colunas = [
    "nome_area",
    "regiao_geopalmas",
    "populacao_estimada",
    "indicador_renda_media",
    "indicador_renda_mediana",
    "cobertura_populacional_renda_pct"
]

print("\n15 MAIORES INDICADORES DE RENDA:")

print(
    gdf.nlargest(
        15,
        "indicador_renda_mediana"
    )[colunas].round(2).to_string(index=False)
)

print("\n15 MENORES INDICADORES DE RENDA:")

print(
    gdf.nsmallest(
        15,
        "indicador_renda_mediana"
    )[colunas].round(2).to_string(index=False)
)

print("\nÁREAS SEM INDICADOR DE RENDA:")

print(
    gdf.loc[
        ~gdf["possui_indicador_renda"],
        colunas
    ].to_string(index=False)
)

print("\nRESUMO POR REGIÃO:")

print(
    gdf.groupby("regiao_geopalmas")
    .agg(
        quantidade_areas=("id_area", "count"),
        populacao_estimada=("populacao_estimada", "sum"),
        areas_com_renda=("possui_indicador_renda", "sum")
    ).round(2).to_string()
)

print("\nArquivos exportados com sucesso.")
