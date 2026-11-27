"""Visão agregada de contratos e licitações."""
import dash
from dash import Input, Output, callback, dcc, html
import plotly.graph_objects as go

from dash_app.components.base import cabecalho, kpi, nota, painel, rodape
from dash_app.components.graficos import ANIMATION_OPTIONS, CORES_GRAFICO as C, aplicar_layout, figura_vazia


dash.register_page(__name__, path="/contratos", name="Contratos e Licitações", order=5)


def _anos():
    anos = set()
    try:
        from src.agents.contratos.loader import carregar_contratos
        anos.update(int(a) for a in carregar_contratos().ano.dropna().unique())
    except Exception:
        pass
    try:
        from src.agents.licitacoes.loader import carregar_licitacoes
        anos.update(int(a) for a in carregar_licitacoes().ano.dropna().unique())
    except Exception:
        pass
    ordenados = sorted(anos)
    return [{"label": str(a), "value": a} for a in ordenados], ordenados


def layout():
    opcoes, anos = _anos()
    ano = anos[-1] if anos else None
    return html.Div([
        cabecalho("Contratos e Licitações", "Acompanhe volumes e valores informados em fontes administrativas distintas."),
        html.Div([html.Span("LEITURA AGREGADA", className="exec-badge"), html.Span("Alertas são triagem cadastral e não conclusão de irregularidade." )], className="exec-status"),
        html.Div([html.Div([html.Label("Exercício", htmlFor="cl-ano"), dcc.Dropdown(id="cl-ano", options=opcoes, value=ano, clearable=False, placeholder="Sem base disponível")], className="exec-filter")], className="exec-filters"),
        html.Div([
            painel("Contratos originais", "Eventos de aditamento e distrato ficam fora da soma do valor original.", html.Div([
                html.Div(id="cl-contratos-kpis", className="exec-kpi-grid exec-kpi-grid-3"),
                dcc.Graph(id="cl-contratos-grafico", figure=figura_vazia("Aguardando base"), animate=True, animation_options=ANIMATION_OPTIONS, config={"displayModeBar": False, "responsive": True}),
                html.Div(id="cl-contratos-aviso", className="exec-inline-note"),
            ], className="page-chart-block")),
            painel("Licitações", "Valores estimados e homologados reportados na base do exercício.", html.Div([
                html.Div(id="cl-licitacoes-kpis", className="exec-kpi-grid exec-kpi-grid-3"),
                dcc.Graph(id="cl-licitacoes-grafico", figure=figura_vazia("Aguardando base"), animate=True, animation_options=ANIMATION_OPTIONS, config={"displayModeBar": False, "responsive": True}),
                html.Div(id="cl-licitacoes-aviso", className="exec-inline-note"),
            ], className="page-chart-block")),
        ], className="page-two-col"),
        painel("Critérios de leitura", "Valores registrados não equivalem a execução financeira.", html.Div([
            html.Div([html.Strong("Contratos"), html.P("O total de valor representa os registros originais. Aditivos não foram somados ao contrato e as somas não representam pagamento." )], className="page-explainer"),
            html.Div([html.Strong("Licitações"), html.P("Diferenças entre estimativa e homologação exigem análise documental; não são prova de sobrepreço ou economia." )], className="page-explainer"),
        ], className="page-explainer-grid")),
        nota("A interface omite contratados, descrições, chaves e linhas individuais, mesmo quando as ferramentas internas conseguem consultá-las."),
        rodape("Bases locais atuais esperadas: atual_contratos.csv e atual_licitacoes.csv. Se não estiverem nesta cópia, os painéis informam a indisponibilidade sem estimar valores."),
    ], className="exec-dashboard page-dashboard")


def _brl(v):
    if v is None or v != v:
        return "—"
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _donut(rotulos, valores):
    fig = go.Figure(go.Pie(labels=rotulos, values=valores, hole=.72, sort=False,
        marker={"colors": [C["acento"], C["secundario"], "#424B42"], "line": {"color": "#171A17", "width": 2}},
        textinfo="none", hovertemplate="%{label}<br>%{value:,}<extra></extra>"))
    aplicar_layout(fig, altura=270, legenda={"orientation": "h", "y": -.08, "x": .12})
    fig.update_layout(showlegend=True)
    return fig


def _barras_modalidades(modalidades):
    fig = go.Figure()
    for chave, nome, cor in [("valor_estimado", "Estimado", C["secundario"]), ("valor_homologado", "Homologado", C["acento"])]:
        fig.add_trace(go.Bar(x=[m.get("modalidade") or "Não informada" for m in modalidades], y=[m.get(chave) for m in modalidades], name=nome, marker_color=cor,
            hovertemplate="%{x}<br>R$ %{y:,.2f}<extra>" + nome + "</extra>"))
    aplicar_layout(fig, altura=300, legenda={"orientation": "h", "y": 1.12, "x": 0})
    fig.update_layout(barmode="group", yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
    return fig


@callback(Output("cl-contratos-kpis", "children"), Output("cl-contratos-grafico", "figure"), Output("cl-contratos-aviso", "children"), Output("cl-licitacoes-kpis", "children"), Output("cl-licitacoes-grafico", "figure"), Output("cl-licitacoes-aviso", "children"), Input("cl-ano", "value"))
def atualizar(ano):
    cards_c, fig_c, aviso_c = [], figura_vazia("Base de contratos indisponível"), ""
    cards_l, fig_l, aviso_l = [], figura_vazia("Base de licitações indisponível"), ""
    try:
        from src.agents.contratos.tools import resumir_contratos
        from src.agents.contratos.auditoria import analisar_aditivos, auditar_contratos
        resumo = resumir_contratos(int(ano))
        aditivos = analisar_aditivos(int(ano))
        auditoria = auditar_contratos(int(ano), limite=1)
        cards_c = [kpi("Contratos originais", f"{resumo['total_contratos']:,}".replace(",", ".")), kpi("Valor original", _brl(resumo["valor_total_original"])), kpi("Sem valor", f"{resumo['contratos_sem_valor']:,}".replace(",", "."))]
        fig_c = _donut(["Em vigor", "Encerrados", "Outras situações"], [resumo["contratos_em_vigor"], resumo["contratos_encerrados"], max(0, resumo["total_contratos"]-resumo["contratos_em_vigor"]-resumo["contratos_encerrados"])])
        aviso_c = f"{aditivos['total_aditivos']} aditivos registrados em contratos originais do exercício; {auditoria['total_registros_com_alerta']} registro(s) com alerta cadastral preliminar. {auditoria['observacao']}"
    except Exception as erro:
        aviso_c = f"Base de contratos indisponível ou inválida ({type(erro).__name__}). Confira Dados e Documentação."
        cards_c = [kpi("Contratos originais", "—"), kpi("Valor original", "—"), kpi("Sem valor", "—")]

    try:
        from src.agents.licitacoes.tools import resumir_licitacoes, comparar_modalidades
        from src.agents.licitacoes.auditoria import auditar_valores_licitacoes
        resumo = resumir_licitacoes(int(ano))
        if resumo.get("status") == "sem_dados":
            raise FileNotFoundError("Sem registros para o exercício")
        modalidades = comparar_modalidades(int(ano))["modalidades"]
        auditoria = auditar_valores_licitacoes(int(ano), limite=1)
        cards_l = [kpi("Processos", f"{resumo['quantidade']:,}".replace(",", ".")), kpi("Homologados", f"{resumo['homologadas']:,}".replace(",", ".")), kpi("Sem valor homologado", f"{resumo['sem_valor_homologado']:,}".replace(",", "."))]
        fig_l = _barras_modalidades(modalidades) if modalidades else figura_vazia("Sem modalidades para este exercício")
        aviso_l = f"Estimado: {_brl(resumo['valor_estimado'])} · homologado: {_brl(resumo['valor_homologado'])}. {auditoria.get('licitacoes_com_alertas', 0)} diferença(s) estimado/homologado sinalizada(s); não constituem prova de irregularidade."
    except Exception as erro:
        aviso_l = f"Base de licitações indisponível ou sem registros neste exercício ({type(erro).__name__}). Confira Dados e Documentação."
        cards_l = [kpi("Processos", "—"), kpi("Homologados", "—"), kpi("Sem valor homologado", "—")]
    if ano is None:
        aviso_c = aviso_l = "Nenhum exercício disponível nas bases locais."
    return cards_c, fig_c, aviso_c, cards_l, fig_l, aviso_l


@callback(Output("cl-contratos-grafico", "animate"), Input("motion-preference", "data"))
def movimento_contratos(reduzido):
    return not bool(reduzido)


@callback(Output("cl-licitacoes-grafico", "animate"), Input("motion-preference", "data"))
def movimento_licitacoes(reduzido):
    return not bool(reduzido)
