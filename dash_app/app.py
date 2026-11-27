"""Aplicação local FinPalmas: navegação, acesso demonstrativo e páginas analíticas."""
from pathlib import Path
import unicodedata

import dash
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
import dash_bootstrap_components as dbc
from flask import abort, send_from_directory


app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="FinPalmas · Inteligência Pública",
    update_title="FinPalmas · carregando",
)

_RAIZ_PROJETO = Path(__file__).resolve().parents[1]
_MAPAS_DIR = _RAIZ_PROJETO / "docs" / "mapas"
_MAPAS_PUBLICADOS = {
    "01_renda_territorial_qualificada.png",
    "02_suporte_analitico.png",
    "03_densidade_demografica.png",
}


@app.server.get("/mapas/<string:nome>")
def servir_mapa(nome):
    """Serve apenas os três mapas agregados documentados no app."""
    if nome not in _MAPAS_PUBLICADOS:
        abort(404)
    return send_from_directory(_MAPAS_DIR, nome, conditional=True)


GRUPOS = {
    "ANÁLISE FISCAL": {"Visão Executiva", "Receitas", "Despesas", "Dívida Ativa"},
    "CONTROLE PÚBLICO": {"Contratos e Licitações", "Auditoria do Agente"},
    "INTELIGÊNCIA E GESTÃO": {"Mapa Territorial", "Assistente", "Governança", "Dados e Documentação"},
}


def menu():
    paginas = sorted(dash.page_registry.values(), key=lambda p: p.get("order", 99))
    itens = [
        html.Div(
            html.Img(
                src="/assets/media/finpalmas-logo.png",
                alt="FinPalmas",
                className="marca-logo",
            ),
            className="marca",
        )
    ]
    for grupo, nomes in GRUPOS.items():
        links = [
            dcc.Link(
                pagina["name"],
                href=pagina["path"],
                id=f"nav-{pagina['module'].rsplit('.', 1)[-1]}",
                className="",
            )
            for pagina in paginas
            if pagina["name"] in nomes
        ]
        if links:
            itens.append(html.Div(grupo, className="nav-grupo-titulo"))
            itens.extend(links)
    itens.append(
        html.Div(
            [html.Span(className="status-ponto"), html.Span("Sessão demonstrativa")],
            className="sidebar-rodape",
        )
    )
    return html.Nav(itens, className="sidebar", **{"aria-label": "Navegação principal"})


def topbar():
    return html.Header(
        [
            html.Div(
                [
                    html.Label("Pesquisar páginas do FinPalmas", htmlFor="global-search", className="visually-hidden"),
                    dcc.Input(
                        id="global-search",
                        type="search",
                        placeholder="Pesquisar seção...",
                        debounce=False,
                        autoComplete="off",
                        className="global-search-input",
                    ),
                    html.Div(id="global-search-results", className="global-search-results"),
                ],
                className="global-search-wrap",
            ),
            html.Details(
                [
                    html.Summary(
                        [html.Span("AD", className="profile-avatar"), html.Span("Administrador", className="profile-label")],
                        title="Perfil demonstrativo",
                    ),
                    html.Div(
                        [
                            html.Strong("Administrador"),
                            html.Small("Acesso demonstrativo"),
                            html.Button("Encerrar sessão", id="access-logout", n_clicks=0, type="button", className="profile-logout"),
                        ],
                        className="profile-dropdown",
                    ),
                ],
                className="profile-menu",
            ),
        ],
        className="topbar",
    )


def layout():
    return html.Div(
        [
            dcc.Location(id="nav-location", refresh=False),
            dcc.Store(id="motion-preference", data=False),
            dcc.Store(id="access-stage", storage_type="session", data="intro"),
            dcc.Interval(id="motion-preference-check", interval=250, max_intervals=1, n_intervals=0),
            dcc.Interval(id="intro-timeout", interval=5650, max_intervals=1, n_intervals=0),
            dcc.Interval(id="intro-transition-timeout", interval=750, max_intervals=1, n_intervals=0, disabled=True),
            html.Div(
                [
                    html.Video(
                        src="/assets/media/finpalmas-abertura-nova.mov",
                        autoPlay=True,
                        muted=True,
                        playsInline=True,
                        preload="auto",
                        className="intro-video",
                        **{"aria-label": "Animação de abertura do FinPalmas"},
                    ),
                ],
                id="access-intro",
                className="access-intro",
            ),
            html.Div(
                [
                    html.Section(
                        [
                            html.Img(src="/assets/media/finpalmas-logo.png", alt="FinPalmas", className="login-logo"),
                            html.Div("INTELIGÊNCIA PÚBLICA · PALMAS/TO", className="login-eyebrow"),
                            html.H1("Acesso ao sistema"),
                            html.P("Entre para visualizar os indicadores e análises de Palmas."),
                            html.Label("Usuário", htmlFor="login-user"),
                            dcc.Input(id="login-user", type="text", placeholder="Digite seu usuário", autoComplete="username", className="login-input"),
                            html.Label("Senha", htmlFor="login-password"),
                            dcc.Input(id="login-password", type="password", placeholder="Digite sua senha", autoComplete="current-password", className="login-input"),
                            html.Div(id="login-notice", className="login-notice", role="status", **{"aria-live": "polite"}),
                            html.Button("Entrar", id="login-submit", n_clicks=0, type="button", className="login-submit"),
                        ],
                        className="login-card",
                    ),
                ],
                id="access-login",
                className="access-login",
            ),
            html.Div(
                [
                    menu(),
                    html.Main(
                        [topbar(), dash.page_container],
                        className="conteudo",
                    ),
                ],
                id="app-shell",
                className="app-shell",
            ),
        ],
        className="access-root",
    )


app.layout = layout


_PAGINAS_NAV = sorted(dash.page_registry.values(), key=lambda p: p.get("order", 99))
app.callback(
    [Output(f"nav-{pagina['module'].rsplit('.', 1)[-1]}", "className") for pagina in _PAGINAS_NAV],
    Input("nav-location", "pathname"),
)(lambda caminho: ["ativo" if pagina["path"] == caminho else "" for pagina in _PAGINAS_NAV])


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(char for char in texto if not unicodedata.combining(char)).casefold().strip()


@app.callback(Output("global-search-results", "children"), Input("global-search", "value"))
def buscar_pagina(termo):
    consulta = _normalizar(termo)
    if not consulta:
        return []
    paginas = sorted(dash.page_registry.values(), key=lambda p: p.get("order", 99))
    encontrados = [pagina for pagina in paginas if consulta in _normalizar(pagina["name"])]
    if not encontrados:
        return html.Div("Nenhuma seção encontrada.", className="search-empty")
    return [
        dcc.Link(
            [html.Strong(pagina["name"]), html.Span(pagina.get("description", ""))],
            href=pagina["path"],
            className="search-result-link",
        )
        for pagina in encontrados
    ]


@app.callback(
    Output("access-stage", "data"),
    Output("login-notice", "children"),
    Output("login-notice", "className"),
    Output("login-user", "value"),
    Output("login-password", "value"),
    Output("intro-transition-timeout", "disabled"),
    Input("intro-timeout", "n_intervals"),
    Input("intro-transition-timeout", "n_intervals"),
    Input("login-submit", "n_clicks"),
    Input("login-password", "n_submit"),
    Input("access-logout", "n_clicks"),
    State("access-stage", "data"),
    State("login-user", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def controlar_acesso(_timer, _transicao, _entrar, _enter, _sair, stage, usuario, senha):
    acionado = ctx.triggered_id
    if acionado == "intro-timeout" and stage == "intro":
        return "transition", "", "login-notice", no_update, no_update, False
    if acionado == "intro-transition-timeout" and stage == "transition":
        return "login", "", "login-notice", no_update, no_update, True
    if acionado == "access-logout":
        return "login", "", "login-notice", "", "", True
    if acionado in {"login-submit", "login-password"}:
        if usuario == "admin" and senha == "12345":
            return "app", "", "login-notice", usuario, "", True
        return "login", "Usuário ou senha incorretos.", "login-notice login-notice-error", no_update, "", True
    return (no_update,) * 6


@app.callback(
    Output("access-intro", "style"),
    Output("access-login", "style"),
    Output("app-shell", "style"),
    Input("access-stage", "data"),
)
def alternar_tela(stage):
    if stage == "app":
        return {"display": "none"}, {"display": "none"}, {}
    if stage == "transition":
        return {"display": "grid", "zIndex": 1001, "animation": "intro-fade-out 750ms ease forwards"}, {"display": "grid", "animation": "login-surface-in 750ms ease forwards"}, {"display": "none"}
    if stage == "login":
        return {"display": "none"}, {"display": "grid"}, {"display": "none"}
    return {"display": "grid"}, {"display": "none"}, {"display": "none"}


app.clientside_callback(
    """function(n) {
        return !!(window.matchMedia && window.matchMedia(
            '(prefers-reduced-motion: reduce)'
        ).matches);
    }""",
    Output("motion-preference", "data"),
    Input("motion-preference-check", "n_intervals"),
)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=8050)
