"""Primitives shared by read-only analytical pages."""
from dash import html


def titulo_secao(titulo, descricao=""):
    return html.Div(
        [
            html.H2(titulo),
            html.Details(
                [
                    html.Summary("i", title="Mais informações", **{"aria-label": f"Mais informações sobre {titulo}"}),
                    html.Div(descricao, className="section-info-copy"),
                ],
                className="section-info",
            ),
        ],
        className="exec-section-heading",
    )


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
            html.Div([titulo_secao(titulo, descricao)], className="exec-section-title"),
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
    return html.Details(
        [
            html.Summary("Critérios e observações", className="method-note-summary"),
            html.P(mensagem, className=f"exec-method-note {tipo}".strip()),
        ],
        className="method-note-disclosure",
    )


def rodape(mensagem):
    return html.Details(
        [
            html.Summary("Limites e cobertura dos dados", className="method-note-summary"),
            html.Footer(mensagem, className="exec-footer-note"),
        ],
        className="method-note-disclosure",
    )
