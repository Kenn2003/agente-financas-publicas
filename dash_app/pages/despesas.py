"""Execução de despesas por exercício a partir da base agregada local."""
import dash
from dash import Input, Output, callback, dcc, html
import plotly.graph_objects as go

from dash_app.components.base import cabecalho, kpi, nota, painel, rodape
from dash_app.components.graficos import ANIMATION_OPTIONS, CORES_GRAFICO as C, aplicar_layout, figura_vazia
from dash_app.services.dados import agregar_despesas_anuais, carregar_despesas


dash.register_page(__name__, path="/despesas", name="Despesas", order=3)
COLUNAS = [("valor_empenho", "Empenhado", C["acento"]), ("valor_liq", "Liquidado", C["neutro"]), ("valor_pago", "Pago", C["secundario"])]


def _opcoes():
    try:
        anos = sorted(int(a) for a in carregar_despesas()["ano_referencia"].unique())
    except Exception:
        anos = []
    return ([{"label": str(a), "value": a} for a in anos], anos)


def _brl(v):
    if v is None or v != v:
        return "—"
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def layout():
    opcoes, anos = _opcoes()
    ano = anos[-1] if anos else None
    return html.Div([
        cabecalho("Despesas", "Leia empenho, liquidação e pagamento separadamente ao longo dos exercícios disponíveis."),
        html.Div([html.Span("BASE AGREGADA", className="exec-badge"), html.Span("Série histórica local; as movimentações recentes dependem de outra fonte." )], className="exec-status"),
        painel("Execução registrada", "Somas por exercício de referência na base consolidada disponível.", html.Div([
            html.Div([html.Div([html.Label("Exercício em foco", htmlFor="des-ano"), dcc.Dropdown(id="des-ano", options=opcoes, value=ano, clearable=False, placeholder="Base indisponível")], className="exec-filter")], className="exec-filters"),
            html.Div([
                html.Div(id="des-kpi-empenhado", children=kpi("Empenhado · soma", "—")),
                html.Div(id="des-kpi-liquidado", children=kpi("Liquidado · soma", "—")),
                html.Div(id="des-kpi-pago", children=kpi("Pago · soma", "—")),
                html.Div(id="des-kpi-negativos", children=kpi("Lançamentos negativos", "—", "Preservados na soma")),
            ], className="exec-kpi-grid exec-kpi-grid-4"),
            html.Div([dcc.Graph(id="des-grafico", figure=figura_vazia("Carregando série"), animate=True,
                animation_options=ANIMATION_OPTIONS,
                config={"displayModeBar": False, "responsive": True}), html.Div(id="des-aviso", className="exec-inline-note exec-inline-note-warning")], className="exec-chart-card"),
            nota("A série mostra somas diretas da base consolidada; valores negativos são preservados. Não há conciliação de estornos, cancelamentos ou restos a pagar. Não compare estas somas diretamente com receitas como se fossem saldo fiscal."),
        ])),
        painel("Como interpretar", "Os três estágios representam movimentos distintos da execução orçamentária.", html.Div([
            html.Div([html.Strong("Empenhado"), html.P("Compromisso registrado na base." )], className="page-explainer"),
            html.Div([html.Strong("Liquidado"), html.P("Movimento de liquidação agregado, conforme o critério de origem." )], className="page-explainer"),
            html.Div([html.Strong("Pago"), html.P("Movimento de pagamento agregado; não equivale a uma conciliação financeira." )], className="page-explainer"),
        ], className="page-explainer-grid")),
        rodape("A camada atual de despesas (2022–2026) exige arquivo CSV próprio e validação; esta tela não mistura bases com critérios diferentes."),
    ], className="exec-dashboard page-dashboard")


def _figura(anual):
    fig = go.Figure()
    for coluna, rotulo, cor in COLUNAS:
        fig.add_trace(go.Scatter(x=anual.ano_referencia, y=anual[coluna], name=rotulo, mode="lines+markers",
            line={"color": cor, "width": 2.5}, marker={"size": 6}, hovertemplate="Exercício %{x}<br>R$ %{y:,.2f}<extra>" + rotulo + "</extra>"))
    aplicar_layout(fig, legenda={"orientation": "h", "y": 1.12, "x": 0})
    fig.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
    return fig


@callback(Output("des-kpi-empenhado", "children"), Output("des-kpi-liquidado", "children"), Output("des-kpi-pago", "children"), Output("des-kpi-negativos", "children"), Output("des-grafico", "figure"), Output("des-aviso", "children"), Input("des-ano", "value"))
def atualizar(ano):
    try:
        dados = carregar_despesas()
    except Exception:
        return (kpi("Empenhado · soma", "—"), kpi("Liquidado · soma", "—"), kpi("Pago · soma", "—"), kpi("Lançamentos negativos", "—"), figura_vazia("Base histórica local indisponível"), "Confira o arquivo Parquet e o esquema esperado. Nenhum valor foi estimado.")
    anual = agregar_despesas_anuais(dados)
    if ano is None:
        return (kpi("Empenhado · soma", "—"), kpi("Liquidado · soma", "—"), kpi("Pago · soma", "—"), kpi("Lançamentos negativos", "—"), _figura(anual), "Selecione um exercício disponível.")
    selecionado = dados.loc[dados.ano_referencia == int(ano)]
    totais = [selecionado[c].sum(min_count=1) for c, _, _ in COLUNAS]
    negativos = sum(int((selecionado[c] < 0).sum()) for c, _, _ in COLUNAS)
    aviso = f"{len(selecionado):,} linhas agregadas na base neste exercício; {negativos:,} valores negativos somados sem exclusão. Verifique os movimentos na fonte antes de interpretar.".replace(",", ".")
    return (*[kpi(f"{nome} · soma", _brl(valor), f"Exercício {ano}") for (_, nome, _), valor in zip(COLUNAS, totais)],
            kpi("Lançamentos negativos", f"{negativos:,}".replace(",", "."), "Nos três campos somados"), _figura(anual), aviso)


@callback(Output("des-grafico", "animate"), Input("motion-preference", "data"))
def respeitar_movimento_reduzido(reduzido):
    return not bool(reduzido)
