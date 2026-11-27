"""Defaults visuais para gráficos Plotly do dashboard."""
import plotly.graph_objects as go


CORES_GRAFICO = {
    "acento": "#C5E86C",
    "neutro": "#D8DED5",
    "secundario": "#8CA7B6",
    "positivo": "#8DCC79",
    "negativo": "#E88278",
    "texto": "#B3B9B0",
    "grade": "#303630",
    "fundo": "rgba(0,0,0,0)",
}
ANIMATION_OPTIONS = {
    "frame": {"duration": 240, "redraw": False},
    "transition": {"duration": 240, "easing": "cubic-in-out"},
}


def figura_vazia(texto, altura=310):
    fig = go.Figure()
    fig.add_annotation(
        text=texto, x=.5, y=.5, xref="paper", yref="paper",
        showarrow=False, font={"size": 14, "color": "#818A80"},
    )
    aplicar_layout(fig, altura=altura)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def aplicar_layout(fig, altura=310, legenda=None, prefixo=None):
    fig.update_layout(
        height=altura,
        margin={"l": 12, "r": 18, "t": 14, "b": 38},
        transition={"duration": 240, "easing": "cubic-in-out"},
        paper_bgcolor=CORES_GRAFICO["fundo"],
        plot_bgcolor=CORES_GRAFICO["fundo"],
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "color": CORES_GRAFICO["texto"], "size": 12},
        hoverlabel={"bgcolor": "#202520", "bordercolor": "#3A4339", "font": {"color": "#F1F3ED", "size": 13}},
        legend=legenda or {"font": {"color": CORES_GRAFICO["texto"]}},
        yaxis_tickprefix=prefixo or "",
    )
    fig.update_xaxes(showgrid=False, linecolor=CORES_GRAFICO["grade"], tickfont={"color": CORES_GRAFICO["texto"]}, automargin=True)
    fig.update_yaxes(showgrid=True, gridcolor=CORES_GRAFICO["grade"], zeroline=False, tickfont={"color": CORES_GRAFICO["texto"]}, automargin=True)
    return fig
