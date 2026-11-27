"""Regras de proteção e limites de uso dos modelos documentados."""
import dash
from dash import html

from dash_app.components.base import cabecalho, kpi, nota, painel, rodape, estado


dash.register_page(__name__, path="/governanca", name="Governança", order=9)


def layout():
    try:
        from src.governance.controle_cobranca import verificar_protecao_iptu_social
        situacao = verificar_protecao_iptu_social(2026)
    except Exception:
        situacao = {"decisao": "revisao_humana", "cobranca_autorizada": False, "motivo": "Não foi possível validar a camada de proteção nesta cópia local."}
    status = "Revisão humana necessária" if situacao.get("decisao") == "revisao_humana" else "Estado conservador"
    return html.Div([
        cabecalho("Governança", "Regras que limitam interpretações automatizadas e deixam explícitos os casos que exigem análise humana."),
        html.Div([html.Span("PROTEÇÃO ATIVA", className="exec-badge"), html.Span("A camada consultada é fail-closed: ausência de informação verificada não libera cobrança." )], className="exec-status exec-status-warning"),
        html.Div([
            kpi("Estado do exercício 2026", status, "Benefício individual não verificado"),
            kpi("Cobrança autorizada", "Não", "A interface não executa cobrança"),
            kpi("Elegibilidade pessoal", "Indeterminada", "A base analítica não possui cadastro administrativo"),
        ], className="exec-kpi-grid exec-kpi-grid-3"),
        painel("Barreira de proteção ao IPTU Social", "A decisão de governança é determinística e separada da resposta do modelo de linguagem.", html.Div([
            html.Div([html.Span("REVISÃO HUMANA", className="page-status-pill"), html.Strong(status)], className="page-protection-title"),
            html.P(situacao.get("motivo", "A situação permanece indeterminada sem validação oficial.")),
            html.P(situacao.get("limitacao", "A base atual não permite verificar elegibilidade individual.")),
            html.P("A avaliação documentada não concede nem revoga benefício e não autoriza operação tributária.", className="exec-method-note"),
        ], className="page-protection", role="status")),
        painel("Decisões possíveis na política", "Os dados desconhecidos mantêm a análise em revisão.", html.Div([
            html.Div([html.Strong("Bloquear"), html.P("Benefício reconhecido oficialmente: impede a continuidade da cobrança no fluxo protegido." )], className="page-explainer"),
            html.Div([html.Strong("Revisão humana"), html.P("Dados ausentes, não verificados ou situação pendente: decisão conservadora implementada para a base disponível." )], className="page-explainer page-explainer-highlight"),
            html.Div([html.Strong("Prosseguir para outros controles"), html.P("Mesmo a verificação negativa não autoriza cobrança: exige os controles adicionais previstos." )], className="page-explainer"),
        ], className="page-explainer-grid")),
        painel("Modelos e equidade experimental", "Os artefatos não foram validados para prever resultados reais.", html.Div([
            html.Div([html.Strong("Rótulos sintéticos"), html.P("Os alvos de inadimplência e recuperabilidade foram criados para experimentar o pipeline. As métricas não demonstram capacidade preditiva no mundo real." )], className="page-explainer"),
            html.Div([html.Strong("Fairness limitada"), html.P("As comparações documentadas usam proxies e características financeiras/temporais dos registros. Não comprovam equidade demográfica nem devem orientar tratamento individual." )], className="page-explainer"),
            html.Div([html.Strong("Revisão jurídica pendente"), html.P("A documentação descreve regras como referência preliminar; a legislação vigente e sua aplicação precisam de validação jurídica antes de qualquer uso administrativo." )], className="page-explainer"),
        ], className="page-explainer-grid")),
        nota("Fontes mantidas: docs/protecao_iptu_social.md, docs/model_card.md, docs/ria_fairness.md e testes de governança. A interface resume essas limitações sem republicar métricas experimentais isoladas."),
        rodape("O orquestrador de IA não recebe atributos pessoais para determinar elegibilidade. A validação oficial e a revisão humana são responsabilidades externas ao protótipo."),
    ], className="exec-dashboard page-dashboard")
