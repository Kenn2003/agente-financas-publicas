"""Série observada de receitas, com comparação apenas em meses comuns."""
import dash
from dash import Input, Output, callback, dcc, html
import plotly.graph_objects as go

from dash_app.components.base import cabecalho, kpi, nota, painel, rodape, estado
from dash_app.components.graficos import ANIMATION_OPTIONS, CORES_GRAFICO as C, aplicar_layout, figura_vazia
from dash_app.services.dados import agregar_receitas, carregar_receitas


dash.register_page(__name__, path="/receitas", name="Receitas", order=2)
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _opcoes():
    try:
        anos = sorted(int(a) for a in carregar_receitas()["ano"].unique())
    except Exception:
        anos = []
    return ([{"label": str(a), "value": a} for a in anos], anos)


def layout():
    opcoes, anos = _opcoes()
    ano = anos[-1] if anos else None
    base = anos[-2] if len(anos) > 1 else ano
    return html.Div([
        cabecalho("Receitas", "Evolução mensal observada e comparação entre exercícios com cobertura comum."),
        html.Div([
            html.Span("BASE LOCAL", className="exec-badge"),
            html.Span("Somente os códigos agregados já adotados na Visão Executiva; sem projeção."),
        ], className="exec-status"),
        painel("Arrecadação registrada", "Soma nominal por mês para os exercícios selecionados.", html.Div([
            html.Div([
                html.Div([html.Label("Exercício em foco", htmlFor="rec-ano"), dcc.Dropdown(id="rec-ano", options=opcoes, value=ano, clearable=False, placeholder="Base indisponível")], className="exec-filter"),
                html.Div([html.Label("Comparar com", htmlFor="rec-base"), dcc.Dropdown(id="rec-base", options=opcoes, value=base, clearable=False, placeholder="Sem exercício base")], className="exec-filter"),
            ], className="exec-filters"),
            html.Div([
                html.Div(id="rec-kpi-total", children=kpi("Total no exercício", "—", "Soma dos meses disponíveis")),
                html.Div(id="rec-kpi-meses", children=kpi("Cobertura da série", "—", "Meses com registro")),
                html.Div(id="rec-kpi-var", children=kpi("Variação nos meses comuns", "—", "Nominal · sem ajuste inflacionário")),
            ], className="exec-kpi-grid exec-kpi-grid-3"),
            html.Div([
                dcc.Graph(id="rec-grafico", figure=figura_vazia("Carregando série"), animate=True,
                          animation_options=ANIMATION_OPTIONS,
                          config={"displayModeBar": False, "responsive": True}),
                html.Div(id="rec-aviso", className="exec-inline-note"),
            ], className="exec-chart-card"),
            nota("Critério: soma de valor_arrecado_mes dos códigos agregados configurados em dash_app/services/dados.py. Valores nominais; a comparação usa apenas os meses presentes em ambos os exercícios e não representa crescimento real."),
        ])),
        rodape("A base local pode estar parcial. A cobertura exibida descreve os registros disponíveis e não confirma completude ou conciliação com a fonte oficial."),
    ], className="exec-dashboard page-dashboard")


def _figura(dados, base, ano):
    fig = go.Figure()
    if not dados.empty:
        fig.add_trace(go.Scatter(x=[MESES[int(m)-1] for m in dados.mes], y=dados.valor_arrecado_mes,
            name=str(ano), mode="lines+markers", line={"color": C["acento"], "width": 3}, marker={"size": 7},
            fill="tozeroy", fillcolor="rgba(197,232,108,.08)", hovertemplate="%{x}<br>R$ %{y:,.2f}<extra>" + str(ano) + "</extra>"))
    if not base.empty:
        fig.add_trace(go.Scatter(x=[MESES[int(m)-1] for m in base.mes], y=base.valor_arrecado_mes,
            name="Comparativo", mode="lines+markers", line={"color": C["secundario"], "width": 2, "dash": "dot"}, marker={"size": 5},
            hovertemplate="%{x}<br>R$ %{y:,.2f}<extra>Comparativo</extra>"))
    aplicar_layout(fig, legenda={"orientation": "h", "y": 1.12, "x": 0})
    fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
    return fig


def _brl(valor):
    if valor is None or valor != valor:
        return "—"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@callback(Output("rec-kpi-total", "children"), Output("rec-kpi-meses", "children"), Output("rec-kpi-var", "children"), Output("rec-grafico", "figure"), Output("rec-aviso", "children"), Input("rec-ano", "value"), Input("rec-base", "value"))
def atualizar(ano, ano_base):
    try:
        base_dados = carregar_receitas()
    except Exception:
        msg = estado("Base de receitas indisponível", "O arquivo agregado local ou seu esquema não pôde ser lido. Confira a seção Dados e Documentação.", "warning")
        return kpi("Total no exercício", "—"), kpi("Cobertura da série", "—"), kpi("Variação nos meses comuns", "—"), figura_vazia("Base local indisponível"), msg
    if ano is None:
        return kpi("Total no exercício", "—"), kpi("Cobertura da série", "—"), kpi("Variação nos meses comuns", "—"), figura_vazia("Sem exercícios disponíveis"), ""
    atual = agregar_receitas(base_dados, int(ano))
    anterior = agregar_receitas(base_dados, int(ano_base)) if ano_base is not None and ano_base != ano else atual.iloc[0:0]
    meses_comuns = sorted(set(atual.mes) & set(anterior.mes))
    a = atual[atual.mes.isin(meses_comuns)].valor_arrecado_mes.sum(min_count=1) if meses_comuns else None
    b = anterior[anterior.mes.isin(meses_comuns)].valor_arrecado_mes.sum(min_count=1) if meses_comuns else None
    variacao = ((a / b) - 1) * 100 if a is not None and b not in (None, 0) else None
    texto_var = f"{variacao:+.1f}%" if variacao is not None else "—"
    nota_var = f"{len(meses_comuns)} meses comuns · comparação nominal" if meses_comuns else "Sem meses comuns para comparar"
    aviso = f"Há registros em {len(atual)} de 12 meses no exercício selecionado. A série local não certifica completude oficial."
    if atual.empty:
        aviso = "Não há registros para o exercício selecionado."
    base_comum = anterior[anterior.mes.isin(meses_comuns)] if meses_comuns else anterior.iloc[0:0]
    atual_comum = atual[atual.mes.isin(meses_comuns)] if meses_comuns else atual.iloc[0:0]
    return (kpi("Total no exercício", _brl(atual.valor_arrecado_mes.sum(min_count=1)) if not atual.empty else "—", "Soma dos meses disponíveis"),
            kpi("Cobertura da série", f"{len(atual)}/12", "Meses com registro"),
            kpi("Variação nos meses comuns", texto_var, nota_var),
            _figura(atual_comum, base_comum, ano), aviso)


@callback(Output("rec-grafico", "animate"), Input("motion-preference", "data"))
def respeitar_movimento_reduzido(reduzido):
    return not bool(reduzido)
