"""Resumo de alertas de qualidade sem divulgar ocorrências individuais."""
import dash
from dash import Input, Output, callback, dcc, html

from dash_app.components.base import cabecalho, kpi, nota, painel, rodape


dash.register_page(__name__, path="/auditoria", name="Auditoria do Agente", order=8)
ANOS = list(range(2022, 2027))


def layout():
    return html.Div([
        cabecalho("Auditoria do Agente", "Triagem agregada de qualidade em três bases administrativas."),
        html.Div([html.Span("TRIAGEM PRELIMINAR", className="exec-badge"), html.Span("Um alerta indica algo a verificar na fonte; não prova fraude, sobrepreço ou irregularidade." )], className="exec-status exec-status-warning"),
        html.Div([html.Label("Exercício", htmlFor="aud-ano"), dcc.Dropdown(id="aud-ano", options=[{"label": str(a), "value": a} for a in ANOS], value=ANOS[-1], clearable=False)], className="exec-filter"),
        painel("Sinais de qualidade", "As ocorrências são contadas no servidor; identificadores e linhas individuais não são enviados à tela.", html.Div(id="aud-resultados", children=html.Div("Selecione um exercício para consultar as fontes disponíveis.", className="page-loading-slot"))),
        painel("Escopo dos testes", "Critérios implementados nas funções de auditoria do projeto.", html.Div([
            html.Div([html.Strong("Despesas"), html.P("Verificações cruzadas entre empenho, liquidação e pagamento. Estornos, cancelamentos e restos a pagar podem explicar diferenças." )], className="page-explainer"),
            html.Div([html.Strong("Contratos"), html.P("Campos ausentes e datas de vigência inconsistentes. A situação jurídica exige análise documental." )], className="page-explainer"),
            html.Div([html.Strong("Licitações"), html.P("Homologação acima do valor estimado. Comparabilidade e contexto precisam ser confirmados na documentação do processo." )], className="page-explainer"),
        ], className="page-explainer-grid")),
        nota("A interface não oferece consulta por número, fornecedor, órgão ou identificador nesta página. Para auditoria formal, use os sistemas e documentos oficiais autorizados."),
        rodape("Nenhum dado pessoal ou identificador de empenho, contrato ou licitação é exposto neste resumo."),
    ], className="exec-dashboard page-dashboard")


@callback(Output("aud-resultados", "children"), Input("aud-ano", "value"))
def atualizar(ano):
    blocos = []
    try:
        from src.agents.despesas.auditoria import auditar_empenhos
        r = auditar_empenhos(int(ano), limite=1)
        if r.get("status") == "ok":
            blocos.append(painel("Execução de despesas", "Base atual · agrupamento por empenho no servidor.", html.Div([
                html.Div([kpi("Empenhos analisados", f"{r['empenhos_analisados']:,}".replace(",", ".")), kpi("Com alerta", f"{r['empenhos_com_alertas']:,}".replace(",", ".")), kpi("Sinais identificados", f"{r['total_alertas']:,}".replace(",", "."))], className="exec-kpi-grid exec-kpi-grid-3"), html.P(r["observacao"], className="exec-method-note")], className="")))
        else:
            blocos.append(kpi("Execução de despesas", "Indisponível", "Fonte atual não encontrada ou sem dados"))
    except Exception:
        blocos.append(kpi("Execução de despesas", "Indisponível", "Fonte atual não encontrada ou inválida"))
    try:
        from src.agents.contratos.auditoria import auditar_contratos
        r = auditar_contratos(int(ano), limite=1)
        blocos.append(html.Div([kpi("Contratos · registros analisados", f"{r['registros_analisados']:,}".replace(",", ".")), kpi("Com alerta cadastral", f"{r['total_registros_com_alerta']:,}".replace(",", ".")), html.P(r["observacao"], className="exec-method-note")], className="page-audit-source") if r.get("status") == "ok" else kpi("Contratos", "Indisponível", "Fonte atual não encontrada ou sem dados"))
    except Exception:
        blocos.append(kpi("Contratos", "Indisponível", "Fonte atual não encontrada ou inválida"))
    try:
        from src.agents.licitacoes.auditoria import auditar_valores_licitacoes
        r = auditar_valores_licitacoes(int(ano), limite=1)
        blocos.append(html.Div([kpi("Licitações · registros analisados", f"{r['licitacoes_analisadas']:,}".replace(",", ".")), kpi("Comparáveis", f"{r['licitacoes_comparaveis']:,}".replace(",", ".")), kpi("Com alerta de valor", f"{r['licitacoes_com_alertas']:,}".replace(",", ".")), html.P(r["observacao"], className="exec-method-note")], className="exec-kpi-grid exec-kpi-grid-3 page-audit-source") if r.get("status") == "ok" else kpi("Licitações", "Indisponível", "Fonte atual não encontrada ou sem dados"))
    except Exception:
        blocos.append(kpi("Licitações", "Indisponível", "Fonte atual não encontrada ou inválida"))
    return html.Div(blocos, className="page-audit-grid")
