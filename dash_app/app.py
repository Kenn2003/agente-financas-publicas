import dash
from dash import Dash, Input, Output, dcc, html
import dash_bootstrap_components as dbc
from flask import abort, send_from_directory
from pathlib import Path

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title="Central de Inteligência Tributária e Auditoria",
)

_MAPAS_DIR = Path(__file__).resolve().parents[1] / "docs" / "mapas"
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
            [
                html.Span(className="marca-simbolo", **{"aria-hidden": "true"}),
                html.Div(
                    [html.Strong("Central Tributária"), html.Small("PALMAS · TO")],
                    className="marca-texto",
                ),
            ],
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
            [html.Span(className="status-ponto"), html.Span("Ambiente local")],
            className="sidebar-rodape",
        )
    )
    return html.Nav(itens, className="sidebar", **{"aria-label": "Navegação principal"})


def layout():
    return html.Div(
        [
            dcc.Location(id="nav-location", refresh=False),
            dcc.Store(id="motion-preference", data=False),
            dcc.Interval(id="motion-preference-check", interval=250, max_intervals=1, n_intervals=0),
            menu(),
            html.Main(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("INTELIGÊNCIA PÚBLICA", className="topbar-sobretitulo"),
                                    html.Span("Palmas · Tocantins", className="topbar-localidade"),
                                ],
                                className="topbar-contexto",
                            ),
                            html.Span("ANÁLISE EXPLORATÓRIA", className="topbar-tag"),
                        ],
                        className="topbar",
                    ),
                    dash.page_container,
                ],
                className="conteudo",
            ),
        ],
        className="app-shell",
    )


app.layout = layout


_PAGINAS_NAV = sorted(dash.page_registry.values(), key=lambda p: p.get("order", 99))
app.callback(
    [Output(f"nav-{pagina['module'].rsplit('.', 1)[-1]}", "className") for pagina in _PAGINAS_NAV],
    Input("nav-location", "pathname"),
)(lambda caminho: ["ativo" if pagina["path"] == caminho else "" for pagina in _PAGINAS_NAV])

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
