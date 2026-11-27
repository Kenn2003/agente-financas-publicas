"""Visão Executiva: agregações observadas dos Parquets locais."""
import dash
from dash import Input, Output, callback, dcc, html
import plotly.graph_objects as go

from dash_app.services.dados import (
    agregar_despesas_anuais,
    agregar_receitas,
    carregar_despesas,
    carregar_receitas,
)


dash.register_page(
    __name__,
    path="/",
    name="Visão Executiva",
    order=1,
)

MESES = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}

CORES = {
    "azul": "#C5E86C",         # destaque principal (verde-lima institucional)
    "azul_escuro": "#101210",
    "verde": "#D8DED5",        # série neutra clara
    "ambar": "#8CA7B6",        # série secundária (azul-aço)
    "texto": "#B3B9B0",
    "grade": "#303630",
}


def _brl(valor):
    if valor is None:
        return "—"
    try:
        if not float(valor) == float(valor):  # NaN
            return "—"
    except (TypeError, ValueError):
        return "—"
    texto = f"R$ {float(valor):,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _anos_e_meses():
    opcoes_receita, ano_receita, opcoes_meses = [], None, []
    opcoes_despesa, ano_despesa = [], None
    mensagens = []

    try:
        receitas = carregar_receitas()
        anos = sorted(int(ano) for ano in receitas["ano"].unique())
        opcoes_receita = [{"label": str(ano), "value": ano} for ano in anos]
        if anos:
            ano_receita = anos[-1]
            meses = sorted(
                int(mes)
                for mes in receitas.loc[receitas["ano"] == ano_receita, "mes"].unique()
            )
            opcoes_meses = [
                {"label": MESES[mes], "value": mes}
                for mes in meses if mes in MESES
            ]
    except Exception as erro:
        mensagens.append(f"Receitas indisponíveis: {type(erro).__name__}.")

    try:
        despesas = carregar_despesas()
        anos = sorted(int(ano) for ano in despesas["ano_referencia"].unique())
        opcoes_despesa = [{"label": str(ano), "value": ano} for ano in anos]
        if anos:
            ano_despesa = anos[-1]
    except Exception as erro:
        mensagens.append(f"Despesas indisponíveis: {type(erro).__name__}.")

    return opcoes_receita, ano_receita, opcoes_meses, opcoes_despesa, ano_despesa, mensagens


def _figura_vazia(mensagem):
    figura = go.Figure()
    figura.add_annotation(
        text=mensagem,
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False,
        font={"size": 14, "color": "#89918A"},
    )
    figura.update_layout(
        height=300,
        margin={"l": 16, "r": 16, "t": 12, "b": 16},
        transition={"duration": 240, "easing": "cubic-in-out"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return figura


def _grafico_layout(figura):
    figura.update_layout(
        height=310,
        margin={"l": 12, "r": 20, "t": 16, "b": 38},
        transition={"duration": 240, "easing": "cubic-in-out"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "color": CORES["texto"], "size": 12},
        hoverlabel={
            "bgcolor": "#202520", "bordercolor": "#3A4339",
            "font": {"color": "#F1F3ED", "size": 13},
        },
        legend={"font": {"color": CORES["texto"]}},
    )
    figura.update_xaxes(showgrid=False, linecolor=CORES["grade"], tickfont={"color": CORES["texto"]}, automargin=True)
    figura.update_yaxes(showgrid=True, gridcolor=CORES["grade"], zeroline=False, tickfont={"color": CORES["texto"]}, automargin=True)
    return figura


def _kpi(rotulo, componente_id, detalhe=""):
    return html.Div(
        [
            html.Div(rotulo, className="exec-kpi-label"),
            html.Div("—", id=componente_id, className="exec-kpi-value"),
            html.Div(detalhe, className="exec-kpi-detail"),
        ],
        className="exec-kpi-card",
    )


def layout():
    (
        opcoes_receita, ano_receita, opcoes_meses,
        opcoes_despesa, ano_despesa, mensagens,
    ) = _anos_e_meses()

    estado = (
        "Bases locais carregadas para leitura. Os totais são somas diretas e ainda exigem validação oficial."
        if not mensagens else " ".join(mensagens)
    )
    estado_classe = "exec-status exec-status-warning" if mensagens else "exec-status"

    return html.Div(
        [
            html.Div(
                [
                    html.Div("INTELIGÊNCIA FISCAL · PALMAS/TO", className="exec-eyebrow"),
                    html.H1("Visão executiva", className="exec-title"),
                    html.P(
                        "Acompanhe receitas e despesas com critérios transparentes, período explícito e ressalvas de qualidade visíveis.",
                        className="exec-subtitle",
                    ),
                ],
                className="exec-heading",
            ),
            html.Div(
                [html.Span("BASE LOCAL", className="exec-badge"), html.Span(estado, id="exec-status-text")],
                className=estado_classe,
                id="exec-status",
            ),
            html.Section(
                [
                    html.Div(
                        [
                            html.Div(
                                [html.H2("Arrecadação registrada"), html.P("Soma exploratória dos códigos agregados documentados no dashboard atual.")],
                                className="exec-section-title",
                            ),
                            html.Div(
                                [
                                    html.Div([html.Label("Exercício"), dcc.Dropdown(id="exec-receita-ano", options=opcoes_receita, value=ano_receita, clearable=False, placeholder="Sem dados")], className="exec-filter"),
                                    html.Div([html.Label("Meses incluídos"), dcc.Dropdown(id="exec-receita-meses", options=opcoes_meses, value=[item["value"] for item in opcoes_meses], multi=True, placeholder="Selecione meses")], className="exec-filter exec-filter-wide"),
                                ],
                                className="exec-filters",
                            ),
                            html.Div(
                                [
                                    _kpi("Total no filtro", "exec-receita-total", "Soma registrada · R$"),
                                    _kpi("Meses com registros", "exec-receita-cobertura", "No exercício selecionado"),
                                    _kpi("Meses no filtro", "exec-receita-selecao", "Período mostrado no gráfico"),
                                ],
                                className="exec-kpi-grid exec-kpi-grid-3",
                            ),
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="exec-receita-grafico",
                                        figure=_figura_vazia("Aguardando seleção de período"),
                                        animate=True,
                                        animation_options={
                                            "frame": {"duration": 240, "redraw": False},
                                            "transition": {"duration": 240, "easing": "cubic-in-out"},
                                        },
                                        config={"displayModeBar": False, "responsive": True},
                                    ),
                                    html.Div(id="exec-receita-aviso", className="exec-inline-note"),
                                ],
                                className="exec-chart-card",
                            ),
                            html.P(
                                "Critério: soma de valor_arrecado_mes para os códigos 1.0.0.0.00.0.0, 2.0.0.0.00.0.0, 7.0.0.0.00.0.0 e 8.0.0.0.00.0.0. A série não representa validação ou conciliação oficial.",
                                className="exec-method-note",
                            ),
                        ],
                        className="exec-panel",
                    )
                ],
                className="exec-section",
            ),
            html.Section(
                [
                    html.Div(
                        [
                            html.Div(
                                [html.H2("Despesas · execução registrada"), html.P("Empenhado, liquidado e pago são apresentados separadamente; não são saldo fiscal conciliado.")],
                                className="exec-section-title",
                            ),
                            html.Div(
                                [html.Label("Exercício de referência"), dcc.Dropdown(id="exec-despesa-ano", options=opcoes_despesa, value=ano_despesa, clearable=False, placeholder="Sem dados")],
                                className="exec-filter",
                            ),
                            html.Div(
                                [
                                    _kpi("Empenhado · soma", "exec-despesa-empenhado", "Registros do exercício"),
                                    _kpi("Liquidado · soma", "exec-despesa-liquidado", "Registros do exercício"),
                                    _kpi("Pago · soma", "exec-despesa-pago", "Registros do exercício"),
                                ],
                                className="exec-kpi-grid exec-kpi-grid-3",
                            ),
                            html.Div(
                                [
                                    dcc.Graph(
                                        id="exec-despesa-grafico",
                                        figure=_figura_vazia("Aguardando dados de despesas"),
                                        animate=True,
                                        animation_options={
                                            "frame": {"duration": 240, "redraw": False},
                                            "transition": {"duration": 240, "easing": "cubic-in-out"},
                                        },
                                        config={"displayModeBar": False, "responsive": True},
                                    ),
                                    html.Div(id="exec-despesa-aviso", className="exec-inline-note exec-inline-note-warning"),
                                ],
                                className="exec-chart-card",
                            ),
                            html.P(
                                "Somas diretas dos registros; valores negativos são preservados. A série não deve ser interpretada como balanço orçamentário conciliado nem comparada diretamente às receitas.",
                                className="exec-method-note",
                            ),
                        ],
                        className="exec-panel",
                    )
                ],
                className="exec-section",
            ),
            html.Footer(
                "Esta tela não apresenta previsão nem recomendação automatizada. Qualquer indicador derivado deve ser validado pela área responsável antes de apoiar uma decisão.",
                className="exec-footer-note",
            ),
        ],
        className="exec-dashboard",
    )


@callback(
    Output("exec-receita-total", "children"),
    Output("exec-receita-cobertura", "children"),
    Output("exec-receita-selecao", "children"),
    Output("exec-receita-grafico", "figure"),
    Output("exec-receita-aviso", "children"),
    Input("exec-receita-ano", "value"),
    Input("exec-receita-meses", "value"),
)
def atualizar_receitas(ano, meses):
    try:
        dados = carregar_receitas()
    except Exception:
        return "—", "—", "—", _figura_vazia("Base de receitas indisponível"), "Confira o arquivo Parquet e as colunas esperadas; nenhum valor foi estimado."
    if ano is None:
        return "—", "—", "—", _figura_vazia("Nenhum exercício disponível"), ""

    mensal_completo = agregar_receitas(dados, int(ano))
    mensal = agregar_receitas(dados, int(ano), meses)
    total = mensal["valor_arrecado_mes"].sum(min_count=1) if not mensal.empty else None
    cobertura = int(mensal_completo["mes"].nunique())
    quantidade_selecionada = 0 if meses is None else len(meses)

    if mensal.empty:
        figura = _figura_vazia("Selecione ao menos um mês com registros")
    else:
        figura = go.Figure(
            go.Bar(
                x=[MESES.get(int(mes), str(mes)) for mes in mensal["mes"]],
                y=mensal["valor_arrecado_mes"],
                marker={"color": CORES["azul"], "line": {"width": 0}},
                hovertemplate="%{x}<br>R$ %{y:,.2f}<extra></extra>",
            )
        )
        figura.update_layout(showlegend=False, yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
        _grafico_layout(figura)

    aviso = f"Há registros em {cobertura} de 12 meses neste exercício. Isso descreve a cobertura da base disponível; não confirma completude da fonte oficial."
    if int(ano) == int(dados["ano"].max()) and cobertura < 12:
        aviso = f"Atenção: o exercício mais recente tem registros em {cobertura} de 12 meses; a soma pode estar incompleta. " + aviso
    return _brl(total), f"{cobertura}/12", f"{quantidade_selecionada}", figura, aviso


@callback(
    Output("exec-despesa-empenhado", "children"),
    Output("exec-despesa-liquidado", "children"),
    Output("exec-despesa-pago", "children"),
    Output("exec-despesa-grafico", "figure"),
    Output("exec-despesa-aviso", "children"),
    Input("exec-despesa-ano", "value"),
)
def atualizar_despesas(ano):
    try:
        dados = carregar_despesas()
    except Exception:
        return "—", "—", "—", _figura_vazia("Base de despesas indisponível"), "Confira o arquivo Parquet e as colunas esperadas; nenhum valor foi estimado."

    anual = agregar_despesas_anuais(dados)
    figura = go.Figure()
    rotulos = {
        "valor_empenho": ("Empenhado", CORES["azul"]),
        "valor_liq": ("Liquidado", CORES["verde"]),
        "valor_pago": ("Pago", CORES["ambar"]),
    }
    for coluna, (nome, cor) in rotulos.items():
        figura.add_trace(
            go.Scatter(
                x=anual["ano_referencia"],
                y=anual[coluna],
                name=nome,
                mode="lines+markers",
                line={"color": cor, "width": 2.5},
                marker={"size": 6},
                hovertemplate="Exercício %{x}<br>R$ %{y:,.2f}<extra>" + nome + "</extra>",
            )
        )
    figura.update_layout(legend={"orientation": "h", "y": 1.12, "x": 0}, yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
    _grafico_layout(figura)

    if ano is None:
        return "—", "—", "—", figura, "Nenhum exercício de despesa disponível."
    selecionado = dados.loc[dados["ano_referencia"] == int(ano)]
    metricas = [selecionado[coluna].sum(min_count=1) for coluna in ("valor_empenho", "valor_liq", "valor_pago")]
    negativos = {
        coluna: int((selecionado[coluna] < 0).sum())
        for coluna in ("valor_empenho", "valor_liq", "valor_pago")
    }
    aviso = (
        f"No exercício selecionado, lançamentos negativos preservados — empenhado: {negativos['valor_empenho']}; "
        f"liquidado: {negativos['valor_liq']}; pago: {negativos['valor_pago']}. "
        "Investigue-os na fonte antes de interpretar variações."
    )
    return *[_brl(valor) for valor in metricas], figura, aviso


@callback(Output("exec-receita-grafico", "animate"), Input("motion-preference", "data"))
def movimento_grafico_receitas(reduzido):
    return not bool(reduzido)


@callback(Output("exec-despesa-grafico", "animate"), Input("motion-preference", "data"))
def movimento_grafico_despesas(reduzido):
    return not bool(reduzido)
