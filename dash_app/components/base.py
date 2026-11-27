"""Primitives shared by read-only analytical pages."""
from dash import html


def cabecalho(titulo, subtitulo="", eyebrow="INTELIGÊNCIA FISCAL · PALMAS/TO"):
    return html.Div(
        [
            html.Div(eyebrow, className="exec-eyebrow"),
            html.H1(titulo, className="exec-title"),
            html.P(subtitulo, className="exec-subtitle"),
        ],
        className="exec-heading",
    )


def selo(tipo):
    """tipo: 'real', 'sintetico' ou 'estimado'."""
    rotulos = {"real": "REGISTRO", "sintetico": "SINTÉTICO", "estimado": "ESTIMADO"}
    return html.Span(rotulos[tipo], className=f"selo {tipo}")


def painel(titulo, descricao, conteudo, class_name=""):
    return html.Section(
        [
            html.Div([html.H2(titulo), html.P(descricao)], className="exec-section-title"),
            conteudo,
        ],
        className=f"exec-panel page-panel {class_name}".strip(),
    )


def kpi(rotulo, valor, detalhe=""):
    return html.Div(
        [
            html.Div(rotulo, className="exec-kpi-label"),
            html.Div(valor, className="exec-kpi-value"),
            html.Div(detalhe, className="exec-kpi-detail"),
        ],
        className="exec-kpi-card",
    )


def estado(titulo, mensagem, tipo="info", acao=None):
    """Estado vazio/indisponível com explicação e recuperação honesta."""
    children = [html.Strong(titulo), html.P(mensagem)]
    if acao:
        children.append(acao)
    return html.Div(children, className=f"page-state page-state-{tipo}", role="status")


def nota(mensagem, tipo=""):
    return html.P(mensagem, className=f"exec-method-note {tipo}".strip())


def rodape(mensagem):
    return html.Footer(mensagem, className="exec-footer-note")
