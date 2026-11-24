import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch

RAIZ = Path(r"C:\Users\kennk\agente-financas-publicas")
PASTA = RAIZ / "data" / "processed"
MAPAS = RAIZ / "docs" / "mapas"

MAPAS.mkdir(parents=True, exist_ok=True)

gdf = gpd.read_file(
    PASTA / "palmas_areas_socioeconomicas_qualificadas.gpkg",
    layer="areas_qualificadas"
).to_crs("EPSG:31982")


def configurar_mapa(ax, titulo):

    ax.set_title(
        titulo,
        fontsize=14,
        fontweight="bold",
        pad=20
    )

    ax.set_axis_off()
    ax.set_aspect("equal")


def salvar_mapa(fig, nome, observacao):

    fig.text(
        0.5,
        0.04,
        "Fontes: IBGE — Censo 2022 e GeoPalmas.\n"
        + observacao,
        ha="center",
        fontsize=9
    )

    fig.savefig(
        MAPAS / nome,
        dpi=300,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.show()


# ==================================================
# MAPA 1 — RENDA TERRITORIAL QUALIFICADA
# ==================================================

limites = [
    0, 1500, 3000, 5000,
    8000, 12000, np.inf
]

rotulos = [
    r"Até R\$ 1.500",
    r"R\$ 1.500 a R\$ 3.000",
    r"R\$ 3.000 a R\$ 5.000",
    r"R\$ 5.000 a R\$ 8.000",
    r"R\$ 8.000 a R\$ 12.000",
    r"Acima de R\$ 12.000"
]

cores = [
    "#ffffcc",
    "#c7e9b4",
    "#7fcdbb",
    "#41b6c4",
    "#2c7fb8",
    "#253494"
]

gdf["faixa_renda"] = pd.cut(
    gdf["indicador_renda_mediana"],
    bins=limites,
    labels=rotulos,
    include_lowest=True
)

qualificados = gdf[
    gdf["suporte_analitico"].isin(
        ["Alto", "Moderado"]
    )
]

fig, ax = plt.subplots(figsize=(12, 16))

legenda = []

for rotulo, cor in zip(rotulos, cores):

    grupo = qualificados[
        qualificados["faixa_renda"].eq(rotulo)
    ]

    if not grupo.empty:
        grupo.plot(
            ax=ax,
            color=cor,
            edgecolor="#555555",
            linewidth=0.3
        )

    legenda.append(
        Patch(facecolor=cor, label=rotulo)
    )

categorias = [
    ("Baixo", "#eeeeee", "Suporte baixo", "///"),
    ("Indisponível", "#aaaaaa", "Sem indicador", None)
]

for categoria, cor, rotulo, hachura in categorias:

    grupo = gdf[
        gdf["suporte_analitico"].eq(categoria)
    ]

    if not grupo.empty:
        grupo.plot(
            ax=ax,
            color=cor,
            edgecolor="#777777",
            linewidth=0.3,
            hatch=hachura
        )

    legenda.append(
        Patch(
            facecolor=cor,
            edgecolor="#777777",
            hatch=hachura,
            label=rotulo
        )
    )

ax.legend(
    handles=legenda,
    title="Indicador mensal de renda",
    loc="upper right",
    fontsize=9
)

configurar_mapa(
    ax,
    "Distribuição territorial da renda — Palmas (TO)\n"
    "Indicadores com suporte alto ou moderado"
)

salvar_mapa(
    fig,
    "01_renda_territorial_qualificada.png",
    "Indicador ponderado das medianas setoriais.\n"
    "Não representa renda individual ou domiciliar per capita."
)


# ==================================================
# MAPA 2 — SUPORTE ANALÍTICO
# ==================================================

fig, ax = plt.subplots(figsize=(12, 16))

cores_suporte = {
    "Alto": "#21866b",
    "Moderado": "#648bb5",
    "Baixo": "#d5a34a",
    "Indisponível": "#b5b5b5"
}

legenda = []

for categoria, cor in cores_suporte.items():

    grupo = gdf[
        gdf["suporte_analitico"].eq(categoria)
    ]

    if not grupo.empty:
        grupo.plot(
            ax=ax,
            color=cor,
            edgecolor="#555555",
            linewidth=0.3
        )

    legenda.append(
        Patch(
            facecolor=cor,
            label=f"{categoria} ({len(grupo)})"
        )
    )

ax.legend(
    handles=legenda,
    title="Suporte analítico",
    loc="upper right"
)

configurar_mapa(
    ax,
    "Qualificação dos indicadores socioeconômicos\n"
    "Palmas — TO"
)

salvar_mapa(
    fig,
    "02_suporte_analitico.png",
    "Classificação exploratória baseada na população estimada "
    "e na cobertura dos dados de renda.\n"
    "Não constitui intervalo de confiança estatística."
)


# ==================================================
# MAPA 3 — DENSIDADE DEMOGRÁFICA
# ==================================================

fig, ax = plt.subplots(figsize=(12, 16))

gdf.plot(
    ax=ax,
    column="densidade_demografica_estimada",
    cmap="YlOrRd",
    edgecolor="#555555",
    linewidth=0.3,
    legend=True,
    legend_kwds={
        "label": "Habitantes estimados por km²",
        "shrink": 0.5
    }
)

configurar_mapa(
    ax,
    "Densidade demográfica estimada — Palmas (TO)\n"
    "Quadras, bairros e loteamentos"
)

salvar_mapa(
    fig,
    "03_densidade_demografica.png",
    "Estimativa por interpolação areal dos setores censitários.\n"
    "Pressupõe distribuição uniforme da população em cada setor."
)

print("=" * 60)
print("MAPAS EXPORTADOS")

for arquivo in sorted(MAPAS.glob("*.png")):
    print(arquivo.name)
