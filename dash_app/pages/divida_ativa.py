"""Estatísticas agregadas de dívida ativa e estado da proteção."""
from datetime import timedelta

import dash
from dash import Input, Output, callback, ctx, dcc, html, no_update
import plotly.graph_objects as go

from dash_app.components.base import cabecalho, kpi, nota, painel, rodape, estado
from dash_app.components.graficos import ANIMATION_OPTIONS, CORES_GRAFICO as C, aplicar_layout, figura_vazia
from dash_app.services.divida_ativa_ml import (
    curvas_sensibilidade,
    diagnosticos_modelos,
    informacoes_modelos,
    simular,
)


dash.register_page(__name__, path="/divida-ativa", name="Dívida Ativa", order=4)


def _anos():
    try:
        from src.agents.divida_ativa.loader import carregar_divida_ativa
        anos = sorted(int(a) for a in carregar_divida_ativa().ano.dropna().unique())
    except Exception:
        anos = []
    return [{"label": str(a), "value": a} for a in anos], anos


def _brl(v):
    if v is None or v != v:
        return "—"
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _figura_matriz(matriz, classes, titulo):
    fig = go.Figure(go.Heatmap(
        z=matriz,
        x=classes,
        y=classes,
        text=matriz,
        texttemplate="%{text}",
        colorscale=[[0, "#1d211d"], [.55, "#52613a"], [1, "#c5e86c"]],
        showscale=False,
        hovertemplate="Real: %{y}<br>Previsto: %{x}<br>Registros: %{z}<extra></extra>",
    ))
    aplicar_layout(fig, altura=250)
    fig.update_layout(title={"text": titulo, "x": .02, "font": {"size": 12}}, margin={"l": 48, "r": 12, "t": 42, "b": 36})
    fig.update_xaxes(title="Previsto", side="bottom")
    fig.update_yaxes(title="Real", autorange="reversed")
    return fig


def _figura_importancias(importancias):
    nomes = {"log_valor_divida": "Log do valor", "idade_divida_dias": "Idade em dias"}
    fig = go.Figure()
    for chave, rotulo, cor in (
        ("inadimplencia", "Inadimplência proxy", C["acento"]),
        ("recuperabilidade", "Recuperabilidade proxy", C["secundario"]),
    ):
        valores = importancias.get(chave, {})
        fig.add_bar(
            name=rotulo,
            x=[nomes.get(feature, feature) for feature in valores],
            y=[100 * valor for valor in valores.values()],
            marker_color=cor,
            hovertemplate="%{x}<br>Importância global: %{y:.1f}%<extra></extra>",
        )
    aplicar_layout(fig, altura=300)
    fig.update_layout(barmode="group", yaxis_title="Importância global (%)", legend={"orientation": "h", "y": 1.12, "x": 0})
    return fig


def _tabela_metricas(metricas):
    nomes = {
        "regressao_logistica": "Regressão Logística · referência",
        "arvore_decisao": "Árvore de Decisão · referência",
        "random_forest": "Random Forest · modelo principal",
    }
    cabecalho = html.Thead(html.Tr([
        html.Th("Modelo", scope="col"),
        html.Th("Acurácia", scope="col"),
        html.Th("Precisão", scope="col"),
        html.Th("Recall", scope="col"),
        html.Th("F1", scope="col"),
    ]))
    linhas = []
    for chave, rotulo in nomes.items():
        m = metricas.get(chave, {})
        linhas.append(html.Tr([
            html.Th(rotulo, scope="row"),
            *[html.Td(f"{m.get(k, 0):.1%}") for k in ("acuracia", "precisao", "recall", "f1")],
        ]))
    return html.Table([cabecalho, html.Tbody(linhas)], className="ml-result-table ml-metrics-table")


def _conteudo_diagnosticos(diagnosticos):
    if not diagnosticos:
        return html.Div("Os diagnósticos não puderam ser carregados dos artefatos locais.", className="ml-result-error", role="status")

    metricas = diagnosticos["metricas_validacao"]
    graficos_validacao = []
    nomes = {
        "regressao_logistica": "Regressão Logística",
        "arvore_decisao": "Árvore de Decisão",
        "random_forest": "Random Forest",
    }
    for chave, nome in nomes.items():
        matriz = metricas.get(chave, {}).get("matriz_confusao_0_1")
        if matriz:
            graficos_validacao.append(dcc.Graph(
                figure=_figura_matriz(matriz, ["Classe 0", "Classe 1"], nome),
                config={"displayModeBar": False, "responsive": True},
            ))

    teste_inad = diagnosticos.get("inadimplencia_teste", {})
    teste_rec = diagnosticos.get("recuperabilidade_teste", {})
    matriz_rec = diagnosticos.get("matriz_recuperabilidade")
    teste_cards = [
        html.Div([
            html.Strong("Random Forest · teste temporal reservado"),
            html.P(
                f"Acurácia {teste_inad.get('acuracia', 0):.1%} · Precisão {teste_inad.get('precisao', 0):.1%} · "
                f"Recall {teste_inad.get('recall', 0):.1%} · F1 {teste_inad.get('f1', 0):.1%}"
            ),
            dcc.Graph(
                figure=_figura_matriz(teste_inad.get("matriz_confusao_0_1", [[0, 0], [0, 0]]), ["Classe 0", "Classe 1"], "Matriz no teste · inadimplência proxy"),
                config={"displayModeBar": False, "responsive": True},
            ),
        ], className="ml-test-card"),
        html.Div([
            html.Strong("Random Forest · recuperabilidade proxy · teste temporal"),
            html.P(f"Acurácia {teste_rec.get('acuracia', 0):.1%} · F1 macro {teste_rec.get('f1_macro', 0):.1%}"),
            dcc.Graph(
                figure=_figura_matriz(matriz_rec or [[0, 0, 0]] * 3, ["Baixa", "Média", "Alta"], "Matriz no teste · recuperabilidade"),
                config={"displayModeBar": False, "responsive": True},
            ),
        ], className="ml-test-card"),
    ]

    return html.Div([
        html.Div([
            html.Strong("Diagnóstico do experimento · alvos sintéticos"),
            html.P("As métricas medem reprodução dos rótulos artificiais no período de validação ou teste. Não medem inadimplência nem recuperação reais."),
        ], className="ml-model-warning", role="note"),
        html.Div([
            html.Div([html.H3("Comparação na validação temporal"), html.P("Os três classificadores foram avaliados na mesma partição de validação."), _tabela_metricas(metricas)], className="ml-diagnostic-block"),
            html.Div([html.H3("Matrizes de confusão · validação"), html.P("Linhas = classe sintética real; colunas = classe prevista."), html.Div(graficos_validacao, className="ml-confusion-grid")], className="ml-diagnostic-block"),
            html.Div([html.H3("Avaliação no teste reservado"), html.P("O conjunto temporal de teste não participou do ajuste. Esses valores continuam sendo apenas sobre alvos sintéticos."), html.Div(teste_cards, className="ml-test-grid")], className="ml-diagnostic-block"),
            html.Div([html.H3("Importância global das variáveis"), html.P("Relevância no modelo Random Forest; não representa causa nem explica isoladamente um cenário individual."), dcc.Graph(figure=_figura_importancias(diagnosticos["importancias"]), config={"displayModeBar": False, "responsive": True})], className="ml-diagnostic-block"),
        ], className="ml-diagnostics-content"),
    ], className="ml-diagnostics")


def _figura_sensibilidade(dados, eixo):
    if eixo == "valor":
        x = dados["valores"]
        titulo_eixo = "Valor hipotético da dívida (R$) · escala logarítmica"
    else:
        x = dados["idades"]
        titulo_eixo = "Idade hipotética da inscrição (dias)"
    fig = go.Figure()
    modelos = {
        "regressao_logistica": ("Regressão Logística", "#e1bd70"),
        "arvore_decisao": ("Árvore de Decisão", "#8ca7b6"),
        "random_forest": ("Random Forest", C["acento"]),
    }
    for chave, (nome, cor) in modelos.items():
        if chave in dados["modelos"]:
            fig.add_scatter(x=x, y=dados["modelos"][chave], name=f"Inadimplência · {nome}", mode="lines", line={"color": cor, "width": 2.5}, hovertemplate="%{x}<br>Score do rótulo 1: %{y:.1%}<extra></extra>")
    for classe, cor in (("baixa", C["negativo"]), ("media", "#8ca7b6"), ("alta", C["positivo"])):
        if classe in dados["recuperabilidade"]:
            fig.add_scatter(x=x, y=dados["recuperabilidade"][classe], name=f"Recuperabilidade · {classe.capitalize()}", mode="lines", line={"color": cor, "width": 1.8, "dash": "dash"}, hovertemplate="%{x}<br>Score da classe: %{y:.1%}<extra></extra>")
    aplicar_layout(fig, altura=340)
    fig.update_layout(yaxis={"title": "Saída do modelo", "range": [0, 1], "tickformat": ".0%"}, legend={"orientation": "h", "y": -0.27, "x": 0, "font": {"size": 10}})
    if eixo == "valor":
        fig.update_xaxes(type="log", title=titulo_eixo, tickprefix="R$ ", tickformat="~s")
    else:
        fig.update_xaxes(title=titulo_eixo)
    return fig


def layout():
    opcoes, anos = _anos()
    ano = anos[-1] if anos else None
    try:
        info_modelos = informacoes_modelos()
        diagnosticos = diagnosticos_modelos()
        referencia_modelos = info_modelos["data_referencia"]
        data_simulada = (referencia_modelos - timedelta(days=365)).isoformat()
        status_modelos = html.P(
            "Artefatos demonstrativos carregados. As saídas são probabilidades/classes "
            "dos alvos sintéticos, não resultados observados.",
            className="ml-model-status ml-model-status-ready",
            role="status",
        )
        texto_metadados = (
            "Variáveis de entrada: log do valor informado e idade da inscrição "
            f"em dias. Referência fixa dos artefatos: {referencia_modelos:%d/%m/%Y}."
        )
    except Exception:
        info_modelos = None
        diagnosticos = None
        referencia_modelos = None
        data_simulada = "2026-01-01"
        status_modelos = html.P(
            "Os artefatos demonstrativos não puderam ser carregados. A simulação "
            "ficará disponível quando os arquivos e dependências estiverem acessíveis.",
            className="ml-model-status ml-model-status-unavailable",
            role="status",
        )
        texto_metadados = "Não foi possível ler os metadados dos artefatos locais."
    return html.Div([
        cabecalho("Dívida Ativa", "Estoque e perfil temporal em nível agregado, com salvaguardas visíveis."),
        html.Div([html.Span("AGREGADO · BASE LOCAL", className="exec-badge"), html.Span("A unidade é registro de dívida; a base não permite contar contribuintes distintos." )], className="exec-status"),
        painel("Retrato da base disponível", "Valores registrados, que podem diferir do saldo atualizado.", html.Div([
            html.Div(id="div-kpis", className="exec-kpi-grid exec-kpi-grid-4"),
            html.Div([html.Label("Ano de inscrição", htmlFor="div-ano"), dcc.Dropdown(id="div-ano", options=opcoes, value=ano, clearable=False, placeholder="Sem base disponível")], className="exec-filter div-year-filter"),
        ])),
        html.Div([
            painel("Valor registrado por mês", "Soma dos registros por mês de inscrição no ano selecionado.", html.Div([
                dcc.Graph(id="div-mensal", figure=figura_vazia("Base de dívida ativa indisponível"), animate=True, animation_options=ANIMATION_OPTIONS, config={"displayModeBar": False, "responsive": True}),
                html.Div(id="div-aviso", className="exec-inline-note"),
            ], className="exec-chart-card div-chart-card")),
            painel("Faixas de valor registradas", "Distribuição por registro, sem identificação de pessoas.", html.Div([
                dcc.Graph(id="div-faixas", figure=figura_vazia("Base de dívida ativa indisponível"), animate=True, animation_options=ANIMATION_OPTIONS, config={"displayModeBar": False, "responsive": True}),
                html.Div(id="div-concentracao", className="exec-inline-note"),
            ], className="exec-chart-card div-chart-card")),
        ], className="page-two-col page-two-col-charts"),
        painel("Simulador de modelos demonstrativos", "Explore um cenário hipotético sem associá-lo a uma inscrição ou pessoa.", html.Div([
            html.Div([
                html.Strong("Demonstração acadêmica · alvos sintéticos"),
                html.P("Os modelos foram treinados com rótulos artificiais derivados de valor e data. Os resultados abaixo não são previsões de inadimplência ou recuperação reais e não devem orientar cobranças ou decisões sobre contribuintes."),
            ], className="ml-model-warning", role="note"),
            status_modelos,
            html.P(texto_metadados, className="ml-model-metadata"),
            html.Div([
                html.Div([
                    html.Label("Valor hipotético da dívida (R$)", htmlFor="div-ml-valor"),
                    dcc.Input(id="div-ml-valor", type="text", value="10000", debounce=True, className="ml-input"),
                ], className="ml-field"),
                html.Div([
                    html.Label("Data hipotética de inscrição", htmlFor="div-ml-data"),
                    dcc.DatePickerSingle(
                        id="div-ml-data",
                        date=data_simulada,
                        min_date_allowed="1900-01-01",
                        max_date_allowed=referencia_modelos.isoformat() if referencia_modelos else None,
                        display_format="DD/MM/YYYY",
                        className="ml-date-picker",
                        clearable=False,
                    ),
                ], className="ml-field"),
                html.Button("Executar demonstração", id="div-ml-executar", n_clicks=0, className="page-button"),
            ], className="ml-simulator-controls"),
            html.Div(
                "Informe valores hipotéticos e execute a demonstração. Nenhum registro da base é usado como entrada.",
                id="div-ml-resultado",
                className="ml-simulator-result",
                role="status",
                **{"aria-live": "polite"},
            ),
            html.Div([
                html.Div([
                    html.H3("Sensibilidade do cenário"),
                    html.P("As curvas variam uma entrada por vez, mantendo a outra fixa. Linhas contínuas: comparação dos classificadores; tracejadas: faixas sintéticas do modelo de recuperabilidade."),
                ], className="ml-sensitivity-heading"),
                html.Div([
                    dcc.Graph(id="div-ml-sensibilidade-valor", figure=figura_vazia("Execute a demonstração para gerar a curva por valor", altura=340), config={"displayModeBar": False, "responsive": True}),
                    dcc.Graph(id="div-ml-sensibilidade-idade", figure=figura_vazia("Execute a demonstração para gerar a curva por idade", altura=340), config={"displayModeBar": False, "responsive": True}),
                ], className="ml-sensitivity-grid"),
            ], className="ml-sensitivity"),
        ], className="ml-simulator")),
        painel("Comparação e diagnóstico dos modelos", "Métricas e matrizes do experimento temporal, mantidas como demonstração de alvos sintéticos.", _conteudo_diagnosticos(diagnosticos)),
        painel("Proteção ao IPTU Social", "O estado é conservador enquanto não houver verificação administrativa oficial.", html.Div(id="div-protecao", children=estado("Revisão humana", "A interface não autoriza cobrança individualizada." , "warning"))),
        painel("Uso responsável", "Limites da base e dos modelos documentados no projeto.", html.Div([
            html.Div([html.Strong("Não é saldo atualizado"), html.P("O resumo usa os valores registrados na base local e pode não refletir atualizações, parcelamentos ou baixas." )], className="page-explainer"),
            html.Div([html.Strong("Sem previsão operacional"), html.P("Os modelos de inadimplência e recuperabilidade foram treinados com alvos sintéticos. Não medem resultados reais nem devem orientar cobrança." )], className="page-explainer"),
        ], className="page-explainer-grid page-explainer-grid-2")),
        nota("Concentração e faixas são por registro, não por contribuinte. Coincidência de valor e data não comprova duplicidade."),
        rodape("A base original contém dados fiscais sensíveis. Esta página usa apenas ferramentas agregadoras e não apresenta registros individuais."),
    ], className="exec-dashboard page-dashboard divida-dashboard")


@callback(Output("div-kpis", "children"), Output("div-mensal", "figure"), Output("div-aviso", "children"), Output("div-faixas", "figure"), Output("div-concentracao", "children"), Output("div-protecao", "children"), Input("div-ano", "value"))
def atualizar(ano):
    try:
        from src.agents.divida_ativa.tools import resumo_divida_ativa, divida_por_mes, distribuicao_faixas, analisar_concentracao, auditar_divida_ativa
        from src.governance.controle_cobranca import verificar_protecao_iptu_social
        resumo = resumo_divida_ativa()
        mensal = divida_por_mes(int(ano))["dados"] if ano is not None else []
        faixas = distribuicao_faixas()
        concentracao = analisar_concentracao()["concentracao"]
        auditoria = auditar_divida_ativa()
        cards = [kpi("Registros", f"{resumo['registros']:,}".replace(",", ".")), kpi("Valor registrado", _brl(resumo["valor_total"])), kpi("Mediana por registro", _brl(resumo["mediana"])), kpi("Período de inscrição", f"{resumo['primeira_inscricao']} — {resumo['ultima_inscricao']}")]
        fig_mes = go.Figure(go.Bar(x=[f"{m['mes']:02d}" for m in mensal], y=[m["valor_total"] for m in mensal], marker_color=C["acento"], hovertemplate="Mês %{x}<br>R$ %{y:,.2f}<extra></extra>")) if mensal else figura_vazia("Sem inscrições nesse ano")
        aplicar_layout(fig_mes)
        fig_mes.update_layout(yaxis_tickprefix="R$ ", yaxis_tickformat="~s")
        fig_faixas = go.Figure(go.Bar(x=[f["faixa"] for f in faixas], y=[f["registros"] for f in faixas], marker={"color": C["secundario"]}, hovertemplate="%{x}<br>%{y:,} registros<extra></extra>"))
        aplicar_layout(fig_faixas, altura=340)
        fig_faixas.update_layout(xaxis_tickangle=-20)
        conc = " · ".join(f"Top {p}% dos registros: {concentracao[f'top_{p}_percentual']['participacao_percentual']:.1f}% do valor registrado" for p in (1, 5, 10))
        aviso = f"{resumo['observacao']} Auditoria: {auditoria['valores_ausentes']} valor(es) ausente(s), {auditoria['valores_negativos']} negativo(s), {auditoria['valores_zerados']} zerado(s)."
        protecao = verificar_protecao_iptu_social(2026)
        painel_protecao = html.Div([
            html.Div([html.Span("REVISÃO HUMANA", className="page-status-pill"), html.Strong("Cobrança não autorizada pela camada de proteção")], className="page-protection-title"),
            html.P(protecao.get("motivo", "Os dados oficiais de benefício não estão disponíveis para validação.")),
            html.P(protecao.get("limitacao", "Sem verificação administrativa individual.")),
        ], className="page-protection", role="status")
        return cards, fig_mes, aviso, fig_faixas, conc + ". " + auditoria["observacao"], painel_protecao
    except Exception as erro:
        aviso = f"Base de dívida ativa indisponível ou inválida ({type(erro).__name__}). Nenhum indicador foi estimado."
        vazio = figura_vazia("Base local indisponível")
        protecao = html.Div([html.Span("REVISÃO HUMANA", className="page-status-pill"), html.Strong("Cobrança não autorizada"), html.P("Sem dados administrativos verificados, a situação permanece indeterminada.")], className="page-protection", role="status")
        return [kpi("Registros", "—"), kpi("Valor registrado", "—"), kpi("Mediana por registro", "—"), kpi("Período de inscrição", "—")], vazio, aviso, vazio, "Indicadores agregados indisponíveis.", protecao


@callback(Output("div-mensal", "animate"), Input("motion-preference", "data"))
def movimento_mensal(reduzido):
    return not bool(reduzido)


@callback(
    Output("div-ml-resultado", "children"),
    Output("div-ml-sensibilidade-valor", "figure"),
    Output("div-ml-sensibilidade-idade", "figure"),
    Input("div-ml-executar", "n_clicks"),
    Input("div-ml-valor", "value"),
    Input("div-ml-data", "date"),
    prevent_initial_call=True,
)
def executar_demonstracao_modelos(n_clicks, valor, data_inscricao):
    # Os campos como Input evitam que valores editados fiquem desatualizados
    # no payload do clique em algumas versões do Dash. Mudanças nos campos
    # apenas atualizam o estado; o cálculo continua explícito pelo botão.
    if ctx.triggered_id != "div-ml-executar":
        return no_update, no_update, no_update
    if not n_clicks:
        return "Informe valores hipotéticos e execute a demonstração. Nenhum registro da base é usado como entrada.", no_update, no_update
    if valor is None or data_inscricao is None:
        pendencias = []
        if valor is None:
            pendencias.append("valor")
        if data_inscricao is None:
            pendencias.append("data")
        return html.Div("Preencha " + " e ".join(pendencias) + " para executar a demonstração.", className="ml-result-error", role="alert"), no_update, no_update
    try:
        valor_texto = str(valor).strip()
        if "," in valor_texto:
            valor_texto = valor_texto.replace(".", "").replace(",", ".")
        resultado = simular(float(valor_texto), data_inscricao)
    except (FileNotFoundError, ModuleNotFoundError):
        return html.Div("Artefatos ou dependências dos modelos não estão disponíveis neste ambiente.", className="ml-result-error", role="alert"), no_update, no_update
    except (TypeError, ValueError, OverflowError) as erro:
        return html.Div(str(erro), className="ml-result-error", role="alert"), no_update, no_update
    except Exception:
        return html.Div("Não foi possível executar a demonstração com os artefatos locais.", className="ml-result-error", role="alert"), no_update, no_update

    curvas = curvas_sensibilidade(float(valor_texto), data_inscricao)

    classes = resultado["probabilidades_recuperabilidade_proxy"]
    ordem = {"baixa": 0, "media": 1, "média": 1, "alta": 2}
    linhas = [
        html.Tr([
            html.Th(classe.capitalize(), scope="row"),
            html.Td(f"{probabilidade:.1%}"),
        ])
        for classe, probabilidade in sorted(
            classes.items(), key=lambda item: ordem.get(item[0].casefold(), 99)
        )
    ]
    return html.Div([
        html.Div([
            html.Span("PROBABILIDADE DO RÓTULO SINTÉTICO 1", className="ml-result-label"),
            html.Strong(f"{resultado['probabilidade_inadimplencia_proxy']:.1%}", className="ml-result-value"),
            html.P("Score do classificador de inadimplência proxy; não é probabilidade de inadimplência real.", className="ml-result-caption"),
            html.Table([
                html.Thead(html.Tr([html.Th("Modelo", scope="col"), html.Th("Score do rótulo 1", scope="col")])),
                html.Tbody([
                    html.Tr([html.Th(nome, scope="row"), html.Td(f"{prob:.1%}")])
                    for nome, prob in (
                        ("Regressão Logística", resultado["probabilidades_inadimplencia_modelos"].get("regressao_logistica", 0)),
                        ("Árvore de Decisão", resultado["probabilidades_inadimplencia_modelos"].get("arvore_decisao", 0)),
                        ("Random Forest", resultado["probabilidades_inadimplencia_modelos"].get("random_forest", 0)),
                    )
                ]),
            ], className="ml-result-table ml-scenario-comparison"),
        ], className="ml-result-card"),
        html.Div([
            html.Span("CLASSES SINTÉTICAS DE RECUPERABILIDADE", className="ml-result-label"),
            html.Table([
                html.Thead(html.Tr([html.Th("Faixa", scope="col"), html.Th("Score do modelo", scope="col")])),
                html.Tbody(linhas),
            ], className="ml-result-table"),
            html.P("Os scores refletem as classes proxy do artefato, não recuperação efetiva nem saldo atualizado.", className="ml-result-caption"),
        ], className="ml-result-card"),
        html.P(
            "Cenário hipotético calculado com a referência fixa dos artefatos: "
            f"{resultado['data_referencia']:%d/%m/%Y}. Não vinculado a uma inscrição real.",
            className="ml-result-footnote",
        ),
    ], className="ml-results-grid"), _figura_sensibilidade(curvas["valor"], "valor"), _figura_sensibilidade(curvas["idade"], "idade")


@callback(Output("div-faixas", "animate"), Input("motion-preference", "data"))
def movimento_faixas(reduzido):
    return not bool(reduzido)
