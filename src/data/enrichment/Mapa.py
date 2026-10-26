import json
import pandas as pd
import plotly.express as px

from ibge import obter_enriquecimento_ibge


# =========================
# ARQUIVOS
# =========================

ARQUIVO_DIVIDA = "relatorio_divida_ativa_com_bairro.csv"
ARQUIVO_MAPA = "bairros_palmas.geojson"


# =========================
# 1. DADOS DO IBGE
# =========================

ibge = obter_enriquecimento_ibge()

print("\nBairros encontrados no IBGE:")
print(ibge[["codigo_bairro_ibge", "bairro"]])


# =========================
# 2. BASE DE DÍVIDA
# =========================

divida = pd.read_csv(
    ARQUIVO_DIVIDA,
    sep=";",
    encoding="utf-8-sig"
)

if "bairro" not in divida.columns:
    raise ValueError(
        "A base de dívida ainda não possui a coluna 'bairro'. "
        "É necessário ligar cada dívida a um bairro antes de gerar o mapa."
    )

divida["Valor Total da Dívida"] = pd.to_numeric(
    divida["Valor Total da Dívida"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False),
    errors="coerce"
)


# =========================
# 3. AGRUPAR POR BAIRRO
# =========================

resumo = (
    divida.groupby("bairro")
    .agg(
        quantidade=("Valor Total da Dívida", "size"),
        valor_total=("Valor Total da Dívida", "sum")
    )
    .reset_index()
)

# Adiciona população e renda do arquivo do Matheus
resumo = resumo.merge(
    ibge[
        [
            "codigo_bairro_ibge",
            "bairro",
            "populacao",
            "rendimento_medio"
        ]
    ],
    on="bairro",
    how="left"
)

print("\nResumo por bairro:")
print(resumo)


# =========================
# 4. GEOJSON
# =========================

with open(
    ARQUIVO_MAPA,
    "r",
    encoding="utf-8"
) as arquivo:
    mapa = json.load(arquivo)


# =========================
# 5. MAPA
# =========================

fig = px.choropleth_map(
    resumo,
    geojson=mapa,
    locations="bairro",
    featureidkey="properties.bairro",
    color="valor_total",
    hover_name="bairro",
    hover_data={
        "quantidade": True,
        "valor_total": ":,.2f",
        "populacao": True,
        "rendimento_medio": ":,.2f"
    },
    map_style="carto-positron",
    center={"lat": -10.18, "lon": -48.33},
    zoom=10,
    title="Valor da dívida ativa por bairro de Palmas"
)

fig.show()
fig.write_html("sprint3_mapa_divida_bairros.html")
