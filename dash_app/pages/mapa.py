"""Explorador territorial e inventário dos desenhos do GeoPalmas."""
import json
import math
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path

import dash
from dash import Input, Output, dcc, html
import plotly.graph_objects as go

from dash_app.components.base import cabecalho, nota, rodape


dash.register_page(
    __name__,
    path="/mapa",
    name="Mapa Territorial",
    title="Mapa Territorial · Palmas",
    order=6,
)

RAIZ = Path(__file__).resolve().parents[2]
GEOJSON_SETORES_IBGE = RAIZ / "data" / "processed" / "ibge_palmas_2022" / "setores_palmas_2022.geojson"


@lru_cache(maxsize=2)
def _ler_setores_cache(caminho, mtime_ns):
    try:
        with Path(caminho).open(encoding="utf-8") as fonte:
            dados = json.load(fonte)
        return dados.get("features", [])
    except (OSError, json.JSONDecodeError):
        return []


def _carregar_setores():
    if not GEOJSON_SETORES_IBGE.is_file():
        return []
    return _ler_setores_cache(str(GEOJSON_SETORES_IBGE), GEOJSON_SETORES_IBGE.stat().st_mtime_ns)


def _numero_propriedade(propriedades, nome):
    valor = propriedades.get(nome)
    try:
        numero = float(valor)
        return numero if math.isfinite(numero) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _quantis(valores):
    ordenados = sorted(valor for valor in valores if valor is not None)
    if not ordenados:
        return []
    cortes = []
    for parte in (0.2, 0.4, 0.6, 0.8):
        posicao = parte * (len(ordenados) - 1)
        inferior = math.floor(posicao)
        superior = math.ceil(posicao)
        valor = ordenados[inferior] + (ordenados[superior] - ordenados[inferior]) * (posicao - inferior)
        if not cortes or valor > cortes[-1]:
            cortes.append(valor)
    return cortes


def _classificar_tema(features, tema):
    props = [feature.get("properties") or {} for feature in features]
    if tema == "renda":
        cores = ["#ffffcc", "#c7e9b4", "#7fcdbb", "#41b6c4", "#2c7fb8", "#253494", "#969696"]
        rotulos = ["Até R$ 1.500", "R$ 1.501–3.000", "R$ 3.001–5.000", "R$ 5.001–8.000", "R$ 8.001–12.000", "Acima de R$ 12.000", "Sem dado"]
        valores = []
        for item in props:
            renda = _numero_propriedade(item, "V06006")
            classe = 6 if renda is None else next((i for i, limite in enumerate((1500, 3000, 5000, 8000, 12000)) if renda <= limite), 5)
            valores.append(classe)
        titulo_escala = "Rendimento mediano mensal · R$ de 2022"
        descricao = "Mediana do rendimento nominal mensal das pessoas responsáveis com rendimento (V06006), em domicílios particulares permanentes ocupados. Não é renda per capita nem dado individual. Valores ausentes permanecem sem dado."
        hover = "Setor %{location}<br>Rendimento mediano: %{customdata[3]}<br>População: %{customdata[2]}<br>Bairro IBGE: %{customdata[0]}<extra></extra>"
    elif tema == "densidade":
        cores = ["#ffffcc", "#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#e31a1c", "#969696"]
        densidades = [_numero_propriedade(item, "densidade_demografica") for item in props]
        cortes = _quantis(densidades)
        valores = [6 if densidade is None else bisect_right(cortes, densidade) for densidade in densidades]
        rotulos = []
        for indice in range(len(cortes) + 1):
            if not cortes:
                rotulos.append("Sem variação")
            elif indice == 0:
                rotulos.append(f"Até {_formatar_numero_pt(cortes[0])}")
            elif indice == len(cortes):
                rotulos.append(f"Acima de {_formatar_numero_pt(cortes[-1])}")
            else:
                rotulos.append(f"{_formatar_numero_pt(cortes[indice - 1])}–{_formatar_numero_pt(cortes[indice])}")
        rotulos.append("Sem dado")
        titulo_escala = "Habitantes por km² · quintis dos setores"
        descricao = "População residente do Censo 2022 (V0001) dividida pela área da geometria do setor calculada em SIRGAS 2000 / UTM 22S (EPSG:31982). Cores em quintis dos setores; o valor exato aparece ao passar o cursor."
        hover = "Setor %{location}<br>Densidade: %{customdata[5]} hab/km²<br>População: %{customdata[2]}<br>Área: %{customdata[6]} km²<br>Bairro IBGE: %{customdata[0]}<extra></extra>"
    else:
        cores = ["#969696", "#d5a34a", "#648bb5", "#21866b"]
        ordem = {"Indisponível": 0, "Baixo": 1, "Moderado": 2, "Alto": 3}
        rotulos = ["Indisponível", "Baixo", "Moderado", "Alto"]
        valores = [ordem.get(item.get("suporte_analitico"), 0) for item in props]
        titulo_escala = "Suporte exploratório por setor"
        descricao = "Classificação descritiva da disponibilidade do indicador e do tamanho populacional do setor: alto (V06006 disponível e população ≥100), moderado (≥30), baixo (<30) e indisponível (sem V06006). Não é intervalo de confiança nem medida validada de precisão."
        hover = "Setor %{location}<br>Suporte: %{customdata[7]}<br>Rendimento mediano: %{customdata[3]}<br>População: %{customdata[2]}<br>Bairro IBGE: %{customdata[0]}<extra></extra>"
    return valores, rotulos, cores, titulo_escala, descricao, hover


def _formatar_renda(valor):
    numero = _numero_propriedade({"v": valor}, "v")
    if numero is None:
        return "Sem dado no setor"
    return "R$ " + f"{numero:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")


def _formatar_numero_pt(valor, casas=0):
    numero = _numero_propriedade({"v": valor}, "v")
    if numero is None:
        return "Sem dado"
    return f"{numero:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def _setor_por_codigo(features, codigo):
    if codigo is None:
        return None
    return next((feature for feature in features if (feature.get("properties") or {}).get("CD_SETOR") == codigo), None)


def _figura_setores(tema, codigo_selecionado=None):
    features = _carregar_setores()
    if not features:
        return go.Figure()
    classes, rotulos, cores, titulo_escala, _, hover = _classificar_tema(features, tema)
    localizacoes, dados_custom = [], []
    for feature in features:
        props = feature.get("properties") or {}
        codigo = props.get("CD_SETOR")
        if not codigo:
            continue
        localizacoes.append(codigo)
        renda = _numero_propriedade(props, "V06006")
        dados_custom.append([
            props.get("NM_BAIRRO") or "Não informado pelo IBGE",
            props.get("NM_DIST") or "Não informado pelo IBGE",
            _formatar_numero_pt(_numero_propriedade(props, "V0001")),
            _formatar_renda(renda),
            _formatar_renda(_numero_propriedade(props, "V06004")),
            _formatar_numero_pt(_numero_propriedade(props, "densidade_demografica")),
            _formatar_numero_pt(_numero_propriedade(props, "area_km2"), 2),
            props.get("suporte_analitico", "Indisponível"),
        ])
    n_cores = len(cores)
    escala = []
    for indice, cor in enumerate(cores):
        escala.extend([[indice / n_cores, cor], [(indice + 1) / n_cores, cor]])
    fig = go.Figure(go.Choropleth(
        geojson={"type": "FeatureCollection", "features": features},
        featureidkey="properties.CD_SETOR",
        locations=localizacoes,
        z=classes,
        zmin=-0.5,
        zmax=n_cores - 0.5,
        colorscale=escala,
        customdata=dados_custom,
        marker={"line": {"color": "rgba(30,38,33,.62)", "width": 0.35}},
        colorbar={
            "title": {"text": titulo_escala, "side": "right", "font": {"size": 10, "color": "#e5e9e3"}},
            "tickmode": "array",
            "tickvals": list(range(len(rotulos))),
            "ticktext": rotulos,
            "tickfont": {"size": 10, "color": "#e5e9e3"},
            "thickness": 15,
            "len": 0.88,
            "outlinewidth": 0,
            "bgcolor": "rgba(20,23,20,.88)",
        },
        hovertemplate=hover,
        showscale=True,
    ))
    selecionado = _setor_por_codigo(features, codigo_selecionado)
    if selecionado:
        geometria = selecionado.get("geometry") or {}
        coordenadas = geometria.get("coordinates") or []
        if geometria.get("type") == "Polygon":
            poligonos = [coordenadas]
        elif geometria.get("type") == "MultiPolygon":
            poligonos = coordenadas
        else:
            poligonos = []
        longitudes, latitudes = [], []
        for poligono in poligonos:
            if not poligono:
                continue
            anel = poligono[0]
            longitudes.extend([ponto[0] for ponto in anel] + [None])
            latitudes.extend([ponto[1] for ponto in anel] + [None])
        if longitudes:
            fig.add_trace(go.Scattergeo(
                lon=longitudes,
                lat=latitudes,
                mode="lines",
                line={"color": "#ffffff", "width": 3},
                hoverinfo="skip",
                showlegend=False,
                name="Setor selecionado",
            ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#141714",
        geo={
            "projection": {"type": "mercator"},
            "fitbounds": "locations",
            "showland": True,
            "landcolor": "#20251f",
            "showocean": True,
            "oceancolor": "#171d20",
            "showlakes": True,
            "lakecolor": "#171d20",
            "showcoastlines": False,
            "showframe": False,
            "bgcolor": "#141714",
        },
        margin={"l": 0, "r": 125, "t": 4, "b": 0},
        height=650,
        clickmode="event",
        hovermode="closest",
        uirevision="palmas-setores-2022",
        dragmode="pan",
    )
    return fig


def _detalhe_setor(codigo, tema):
    features = _carregar_setores()
    feature = _setor_por_codigo(features, codigo)
    total_setores = len(features)
    com_renda = sum(_numero_propriedade(f.get("properties") or {}, "V06006") is not None for f in features)
    if not feature:
        return html.Div([
            html.Div([html.Span("SETOR SELECIONADO", className="map-meta-label"), html.Strong("Clique em um setor para consultar os dados", className="map-file-name")], className="map-meta-block"),
            html.Div([html.Span("Cobertura da camada", className="map-meta-label"), html.Strong(f"{total_setores} setores censitários · 2022")], className="map-meta-block"),
            html.Div([html.Span("Rendimento", className="map-meta-label"), html.Strong(f"{com_renda} setores com mediana disponível")], className="map-meta-block"),
        ], className="map-inspector-content", role="status", **{"aria-live": "polite"})
    props = feature.get("properties") or {}
    populacao = _numero_propriedade(props, "V0001")
    renda_media = _numero_propriedade(props, "V06004")
    renda_mediana = _numero_propriedade(props, "V06006")
    densidade = _numero_propriedade(props, "densidade_demografica")
    area = _numero_propriedade(props, "area_km2")
    suporte = props.get("suporte_analitico") or "Indisponível"

    def linha(rotulo, valor):
        return html.Div([html.Span(rotulo, className="map-meta-label"), html.Strong(valor)], className="map-meta-block")

    return html.Div([
        linha("CÓDIGO DO SETOR IBGE", str(props.get("CD_SETOR", codigo))),
        linha("Bairro informado pelo IBGE", str(props.get("NM_BAIRRO") or "Não informado")),
        linha("Distrito", str(props.get("NM_DIST") or "Não informado")),
        linha("População residente · 2022", _formatar_numero_pt(populacao)),
        linha("Rendimento mediano dos responsáveis", _formatar_renda(renda_mediana)),
        linha("Rendimento médio dos responsáveis", _formatar_renda(renda_media)),
        linha("Densidade demográfica", f"{_formatar_numero_pt(densidade)} hab/km²" if densidade is not None else "Sem dado"),
        linha("Área geométrica do setor", f"{_formatar_numero_pt(area, 2)} km²" if area is not None else "Sem dado"),
        linha("Suporte analítico exploratório", suporte),
        html.P("Valores de rendimento são nominais de 2022, referentes às pessoas responsáveis com rendimento. Não descrevem indivíduos, renda per capita ou elegibilidade a benefícios.", className="map-honesty-note"),
    ], className="map-inspector-content", role="status", **{"aria-live": "polite"})


def _area_anular(anel):
    if len(anel) < 4:
        return 0.0
    return abs(sum(
        anel[i][0] * anel[i + 1][1] - anel[i + 1][0] * anel[i][1]
        for i in range(len(anel) - 1)
    ) / 2)


def _area_poligono(anelos):
    if not anelos:
        return 0.0
    return max(0.0, _area_anular(anelos[0]) - sum(_area_anular(anel) for anel in anelos[1:]))


def _selecao_do_clique(click_data, chave):
    """Extrai customdata do evento do Plotly sem deixar payloads parciais quebrarem o painel."""
    if not isinstance(click_data, dict):
        return None
    pontos = click_data.get("points")
    if not isinstance(pontos, list) or not pontos or not isinstance(pontos[0], dict):
        return None
    custom = pontos[0].get("customdata")
    if not isinstance(custom, (list, tuple)) or len(custom) < 4 or custom[3] != chave:
        return None
    try:
        indice, area = int(custom[0]), float(custom[1])
    except (TypeError, ValueError, OverflowError):
        return None
    if indice < 1 or not math.isfinite(area):
        return None
    rotulo_lote = str(custom[2]).strip() if len(custom) > 2 and custom[2] is not None else ""
    return indice, area, rotulo_lote


def _figura_camada(features, chave, face_selecionada=None):
    fig = go.Figure()
    pontos_x, pontos_y = [], []
    areas = []
    grupos = {
        True: {"x": [], "y": [], "customdata": []},
        False: {"x": [], "y": [], "customdata": []},
    }
    areas_com_rotulo = 0
    geometria_selecionada = None
    for indice, feature in enumerate(features, start=1):
        geometria = feature.get("geometry") or {}
        if geometria.get("type") != "Polygon":
            continue
        anelos = geometria.get("coordinates") or []
        if not anelos or not anelos[0]:
            continue
        area = _area_poligono(anelos)
        areas.append(area)
        exterior = anelos[0]
        propriedades = feature.get("properties") or {}
        if indice == face_selecionada:
            geometria_selecionada = exterior
        rotulo_lote = str(propriedades.get("lote_Text") or "").strip()
        areas_com_rotulo += int(bool(rotulo_lote))
        grupo = grupos[bool(rotulo_lote)]
        pontos_x.extend(ponto[0] for ponto in exterior)
        pontos_y.extend(ponto[1] for ponto in exterior)
        grupo["x"].extend(ponto[0] for ponto in exterior)
        grupo["y"].extend(ponto[1] for ponto in exterior)
        grupo["customdata"].extend([[indice, area, rotulo_lote or "Sem rótulo associado", chave]] * len(exterior))
        grupo["x"].append(None)
        grupo["y"].append(None)
        grupo["customdata"].append([None, None, None, None])
    estilos = {
        True: ("rgba(197,232,108,.16)", "rgba(197,232,108,.88)"),
        False: ("rgba(226,157,96,.18)", "rgba(231,179,134,.92)"),
    }
    for tem_rotulo, grupo in grupos.items():
        if not any(valor is not None for valor in grupo["x"]):
            continue
        preenchimento, contorno = estilos[tem_rotulo]
        fig.add_trace(go.Scatter(
            x=grupo["x"], y=grupo["y"],
            mode="lines", fill="toself", fillcolor=preenchimento,
            line={"color": contorno, "width": 0.85},
            customdata=grupo["customdata"],
            hoveron="points+fills",
            hovertemplate="Face CAD %{customdata[0]}<br>Lote: %{customdata[2]}<br>Área planimétrica: %{customdata[1]:,.1f} u²<extra></extra>",
            showlegend=False,
        ))
    if geometria_selecionada:
        fig.add_trace(go.Scatter(
            x=[ponto[0] for ponto in geometria_selecionada] + [None],
            y=[ponto[1] for ponto in geometria_selecionada] + [None],
            mode="lines", fill="toself", fillcolor="rgba(255,255,255,.28)",
            line={"color": "#ffffff", "width": 3},
            hoverinfo="skip", showlegend=False, name="Face selecionada",
        ))
    if pontos_x and pontos_y:
        fig.update_xaxes(visible=False, range=[min(pontos_x), max(pontos_x)], constrain="domain")
        fig.update_yaxes(visible=False, range=[min(pontos_y), max(pontos_y)], scaleanchor="x", scaleratio=1)
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#141714", plot_bgcolor="#141714",
        margin={"l": 0, "r": 0, "t": 0, "b": 0}, height=650,
        dragmode="pan", clickmode="event", hovermode="closest", showlegend=False,
        uirevision=f"camada-{chave}",
    )
    return fig, areas, areas_com_rotulo


def _opcoes_subareas(regiao):
    itens = [item for item in CATALOGO_DWGS if item.get("regiao") == regiao]
    return [
        {"label": item.get("chave_subarea_arquivo", ""), "value": item.get("chave_subarea_arquivo", "")}
        for item in itens
    ]


def _detalhe_subarea(chave, click_data=None):
    item = next((linha for linha in CATALOGO_DWGS if linha.get("chave_subarea_arquivo") == chave), None)
    if not item:
        return html.Div("Selecione uma subárea para consultar o arquivo de origem.", className="map-inspector-empty")
    caminho = item.get("caminho_local", "")
    arquivo_existe = (RAIZ / caminho).is_file() if caminho else False
    children = [
        html.Div([html.Span("DESENHO DE ORIGEM", className="map-meta-label"), html.Strong(item.get("arquivo_original", "—"), className="map-file-name")], className="map-meta-block"),
        html.Div([html.Span("Região", className="map-meta-label"), html.Strong(item.get("regiao", "—"))], className="map-meta-block"),
        html.Div([html.Span("Tamanho", className="map-meta-label"), html.Strong(f"{int(item.get('tamanho_bytes') or 0) / 1_000_000:.2f} MB")], className="map-meta-block"),
        html.Div([html.Span("Arquivo local", className="map-meta-label"), html.Strong("Disponível" if arquivo_existe else "Ausente")], className="map-meta-block"),
    ]
    features = _carregar_features(chave)
    if features:
        total_com_rotulo = sum(bool(str((feature.get("properties") or {}).get("lote_Text") or "").strip()) for feature in features)
        children.insert(1, html.Div([html.Span("Camada derivada", className="map-meta-label"), html.Strong(f"{chave} · polígonos convertidos")], className="map-meta-block"))
        selecionado = _selecao_do_clique(click_data, chave)
        if selecionado:
            children.extend([
                html.Div([html.Span("GEOMETRIA SELECIONADA", className="map-meta-label"), html.Strong(f"Face CAD {selecionado[0]}")], className="map-meta-block map-selected-feature"),
                html.Div([html.Span("Rótulo de lote", className="map-meta-label"), html.Strong(selecionado[2] or "Sem rótulo associado")], className="map-meta-block"),
                html.Div([html.Span("Área planimétrica", className="map-meta-label"), html.Strong(f"{selecionado[1]:,.1f} unidades²")], className="map-meta-block"),
            ])
        else:
            children.append(html.Div([html.Span("Rótulos associados", className="map-meta-label"), html.Strong(f"{total_com_rotulo} de {len(features)} faces com número de lote")], className="map-meta-block"))
        children.append(html.Div([html.Span("Sistema de coordenadas", className="map-meta-label"), html.Strong("Não informado no DXF")], className="map-meta-block"))
    else:
        children.append(html.Div([html.Span("Geometria", className="map-meta-label"), html.Strong("Conversão ainda não feita para esta subárea")], className="map-meta-block"))
    return html.Div(children, className="map-inspector-content")


def _mapa_indisponivel(chave):
    features = _carregar_features(chave)
    if features:
        figura, areas, com_rotulo = _figura_camada(features, chave)
        return html.Div([
            dcc.Graph(id="map-geometry-graph", figure=figura, config={
                "responsive": True, "scrollZoom": True, "displaylogo": False,
                "modeBarButtonsToAdd": ["select2d", "lasso2d"],
                "toImageButtonOptions": {"format": "png", "filename": f"mapa-{chave}"},
            }, className="map-interactive-graph"),
            html.Div([
                html.Span(className="map-legend-swatch map-legend-has-label", **{"aria-hidden": "true"}),
                html.Span("Com número de lote"),
                html.Span(className="map-legend-swatch map-legend-no-label", **{"aria-hidden": "true"}),
                html.Span("Sem rótulo associado"),
                html.Span("Qualidade do vínculo CAD · não é renda ou zoneamento", className="map-legend-note"),
            ], className="map-pilot-legend", role="note", **{"aria-label": "Legenda da qualidade dos rótulos CAD"}),
            html.Div([
                html.Span(f"{len(areas)} faces CAD", className="map-status-chip"),
                html.Span(f"{com_rotulo} rótulos ligados", className="map-status-chip"),
                html.Span("Arraste para mover · role para aproximar", className="map-status-chip"),
                html.Span("Clique numa forma para inspecionar", className="map-status-chip"),
            ], className="map-status-list map-pilot-controls"),
            html.P("Visualização piloto em coordenadas locais do CAD. O DXF não informa CRS; a posição não está georreferenciada e as unidades de área são desconhecidas.", className="map-honesty-note map-pilot-note"),
        ], className="map-pilot-state")
    if chave:
        detalhe = "O desenho está catalogado, mas ainda não foi convertido para uma camada vetorial. Converta o DWG para DXF e processe-o para revisar os polígonos e rótulos."
    else:
        detalhe = "Selecione uma subárea do catálogo. Para desenhar limites, o arquivo precisa ser convertido para DXF e revisado como polígonos."
    return html.Div([
        html.Div([
            html.Div(className="map-empty-mark", **{"aria-hidden": "true"}),
            html.H2("Camada vetorial em preparação"),
            html.P(detalhe),
            html.Div([
                html.Span("209 DWGs no catálogo", className="map-status-chip"),
                html.Span("CRS ainda não validado", className="map-status-chip"),
                html.Span("Indicadores não vinculados", className="map-status-chip"),
            ], className="map-status-list"),
            html.P("Nenhum limite é desenhado aqui até que a conversão, o sistema de coordenadas e o fechamento dos polígonos sejam conferidos.", className="map-honesty-note"),
        ], className="map-empty-state", role="status"),
        dcc.Graph(id="map-geometry-graph", figure=go.Figure(), style={"display": "none"}),
    ])


def layout():
    setores = _carregar_setores()
    populacao = sum((_numero_propriedade((feature.get("properties") or {}), "V0001") or 0) for feature in setores)
    renda_disponivel = sum(_numero_propriedade((feature.get("properties") or {}), "V06006") is not None for feature in setores)
    figura = _figura_setores("renda") if setores else go.Figure()
    return html.Div([
        cabecalho("Mapa Territorial", "Explore os setores censitários de Palmas e alterne entre indicadores territoriais do Censo 2022."),
        html.Div([
            html.Div([html.Span("GEOMETRIA OFICIAL", className="map-summary-label"), html.Strong(f"{len(setores):,}".replace(",", "."), className="map-summary-value"), html.Span("setores censitários do IBGE", className="map-summary-caption")], className="map-summary"),
            html.Div([html.Span("POPULAÇÃO · 2022", className="map-summary-label"), html.Strong(_formatar_numero_pt(round(populacao)), className="map-summary-value"), html.Span("residentes em Palmas no Censo", className="map-summary-caption")], className="map-summary"),
            html.Div([html.Span("RENDIMENTO DISPONÍVEL", className="map-summary-label"), html.Strong(f"{renda_disponivel}/{len(setores)}", className="map-summary-value map-summary-value-small"), html.Span("setores com mediana publicada", className="map-summary-caption")], className="map-summary"),
        ], className="map-summary-row"),
        html.Div([
            html.Section([
                html.Div([
                    html.Div([html.H2("Palmas · setores censitários"), html.P("Selecione um tema e clique em qualquer setor para consultar os valores e a fonte.")], className="map-workspace-heading"),
                    html.Div([
                        html.Label("Tema do mapa", htmlFor="map-theme"),
                        dcc.Dropdown(
                            id="map-theme",
                            options=[
                                {"label": "Rendimento territorial", "value": "renda"},
                                {"label": "Densidade demográfica", "value": "densidade"},
                                {"label": "Suporte analítico", "value": "suporte"},
                            ],
                            value="renda", clearable=False, searchable=False,
                            className="map-dropdown map-theme-dropdown",
                        ),
                    ], className="map-filter map-theme-filter"),
                ], className="map-workspace-toolbar"),
                html.Div(id="map-theme-description", className="map-theme-description"),
                dcc.Loading(
                    dcc.Graph(
                        id="map-ibge-graph", figure=figura,
                        config={"responsive": True, "scrollZoom": True, "displaylogo": False,
                                "toImageButtonOptions": {"format": "png", "filename": "palmas-setores-censo-2022"}},
                        className="map-interactive-graph",
                    ), type="circle", color="#c5e86c",
                ) if setores else html.Div([
                    html.H2("Dados cartográficos não preparados"),
                    html.P("Execute src/governance/preparar_mapa_setores_ibge.py para gerar a camada local a partir dos insumos oficiais em data/raw/ibge_2022/.")
                ], className="map-empty-state", role="alert"),
                html.Div([
                    html.Span("FONTE", className="map-meta-label"),
                    html.A("IBGE · Malha de Setores Censitários 2022", href="https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/gpkg/UF/TO/TO_setores_CD2022.gpkg", target="_blank", rel="noopener noreferrer"),
                    html.Span("EPSG:4674 · medidas em EPSG:31982", className="map-source-count"),
                ], className="map-workspace-footer"),
            ], className="exec-panel map-workspace"),
            html.Aside([
                html.Div([html.Span("DETALHE DO SETOR", className="map-inspector-eyebrow"), html.H2("Censo 2022"), html.P("Selecione uma geometria para ver os indicadores.")], className="map-inspector-heading"),
                html.Div(id="map-sector-inspector", children=_detalhe_setor(None, "renda")),
            ], className="exec-panel map-inspector"),
        ], className="map-explorer-grid"),
        html.Div(id="map-theme-method", className="map-method-note"),
        nota("Metadados completos e regras dos indicadores: docs/metodologia_geoespacial.md e data/processed/ibge_palmas_2022/metadados.json."),
        rodape("É vedado inferir elegibilidade ao IPTU Social, renda individual ou prioridade de cobrança a partir destes mapas."),
    ], className="exec-dashboard page-dashboard map-page")


@dash.callback(Output("map-ibge-graph", "figure"), Input("map-theme", "value"), Input("map-ibge-graph", "clickData"))
def atualizar_figura_setores(tema, click_data):
    codigo = None
    try:
        ponto = click_data["points"][0]
        codigo = ponto.get("location") if isinstance(ponto, dict) else None
    except (KeyError, IndexError, TypeError):
        pass
    return _figura_setores(tema or "renda", codigo)


@dash.callback(Output("map-sector-inspector", "children"), Input("map-theme", "value"), Input("map-ibge-graph", "clickData"))
def atualizar_detalhe_setor(tema, click_data):
    codigo = None
    try:
        ponto = click_data["points"][0]
        codigo = ponto.get("location") if isinstance(ponto, dict) else None
    except (KeyError, IndexError, TypeError):
        pass
    return _detalhe_setor(codigo, tema or "renda")


@dash.callback(Output("map-theme-description", "children"), Output("map-theme-method", "children"), Input("map-theme", "value"))
def atualizar_descricao_tema(tema):
    _, _, _, titulo_escala, descricao, _ = _classificar_tema(_carregar_setores(), tema or "renda")
    return html.P(descricao), html.Div([
        html.Strong(titulo_escala),
        html.P("Geometria IBGE em EPSG:4674; população e rendimento vinculados pelo código oficial CD_SETOR. Áreas calculadas após reprojeção para EPSG:31982. Valores ausentes são mostrados em cinza, nunca como zero."),
    ])
