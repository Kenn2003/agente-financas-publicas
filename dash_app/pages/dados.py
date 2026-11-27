"""Inventário local de fontes esperadas, sem abrir valores ou registros."""
from pathlib import Path

import dash
from dash import html

from dash_app.components.base import cabecalho, kpi, nota, painel, rodape


dash.register_page(__name__, path="/dados", name="Dados e Documentação", order=10)
RAIZ = Path(__file__).resolve().parents[2]
FONTES = [
    ("Receitas · agregado", "data/ready/receitas_recentes.parquet", "Parquet agregado utilizado pela Visão Executiva e Receitas.", "A cobertura anual pode ser parcial."),
    ("Despesas · histórico", "data/ready/gastos_diretos.parquet", "Série consolidada de empenho, liquidação e pagamento.", "Valores negativos são preservados; não há reconciliação fiscal."),
    ("Despesas · atual", "data/raw/csv/atual_despesas.csv", "Movimentações dos exercícios de 2022 a 2026.", "Base independente; não misturar com o Parquet histórico."),
    ("Contratos", "data/raw/csv/atual_contratos.csv", "Contratos originais, aditivos e distratos.", "Interface só apresenta agregados; valores não equivalem a despesas pagas."),
    ("Licitações", "data/raw/csv/atual_licitacoes.csv", "Processos e valores estimados/homologados.", "Comparações de valor não comprovam sobrepreço ou economia."),
    ("Dívida ativa", "relatorio_dívida_ativa.csv", "Fonte agregada pelo serviço de dívida ativa.", "Contém informação fiscal sensível e não tem identificador de inscrição estável."),
    ("Mapas territoriais", "docs/mapas/01_renda_territorial_qualificada.png", "Produtos visuais agregados derivados do Censo 2022 e GeoPalmas.", "Estimativas parciais; consulte a metodologia antes de interpretar."),
]


def _inventario():
    linhas = []
    disponiveis = 0
    for nome, relativo, uso, limitacao in FONTES:
        arquivo = RAIZ / relativo
        encontrado = arquivo.is_file()
        disponiveis += int(encontrado)
        status = "Disponível localmente" if encontrado else "Não encontrado nesta cópia"
        classe = "page-source-state page-source-ok" if encontrado else "page-source-state page-source-missing"
        linhas.append(html.Tr([
            html.Th(nome, scope="row"),
            html.Td(html.Span(status, className=classe)),
            html.Td(uso),
            html.Td(limitacao),
        ]))
    tabela = html.Table([
        html.Thead(html.Tr([html.Th("Fonte", scope="col"), html.Th("Estado", scope="col"), html.Th("Uso nesta interface", scope="col"), html.Th("Limite", scope="col")])) ,
        html.Tbody(linhas),
    ], className="page-source-table")
    return tabela, disponiveis


def layout():
    tabela, disponiveis = _inventario()
    total = len(FONTES)
    return html.Div([
        cabecalho("Dados e Documentação", "Inventário das fontes esperadas e limites de uso da cópia local."),
        html.Div([html.Span("VERIFICAÇÃO LOCAL", className="exec-badge"), html.Span("A presença de arquivo não comprova atualização, completude, autenticidade ou autorização de uso." )], className="exec-status"),
        html.Div([
            kpi("Fontes listadas", str(total), "Inventário do dashboard"),
            kpi("Disponíveis nesta cópia", f"{disponiveis}/{total}", "Verificação de existência do arquivo"),
            kpi("Atualização confirmada", "Não", "Nenhuma conexão de atualização automática"),
        ], className="exec-kpi-grid exec-kpi-grid-3"),
        painel("Fontes monitoradas", "O inventário verifica somente caminhos locais e não lê amostras nem conteúdo de registros.", html.Div(tabela, className="page-table-wrap")),
        painel("Documentação de referência", "Estes documentos mantêm metodologia, limites e regras do projeto.", html.Div([
            html.Div([html.Strong("Metodologia territorial"), html.P("docs/metodologia_geoespacial.md · fontes, interpolação, cobertura e limitações dos mapas." )], className="page-explainer"),
            html.Div([html.Strong("Modelos e equidade"), html.P("docs/model_card.md e docs/ria_fairness.md · os rótulos do modelo são sintéticos." )], className="page-explainer"),
            html.Div([html.Strong("Proteção IPTU Social"), html.P("docs/protecao_iptu_social.md · decisão fail-closed e revisão humana." )], className="page-explainer"),
        ], className="page-explainer-grid")),
        nota("Dados processados e arquivos públicos podem continuar contendo informações protegidas. A interface só deve consumir ferramentas agregadas e fontes explicitamente autorizadas."),
        rodape("Status calculado ao abrir a página. A aplicação não consulta APIs externas e não confirma atualização junto às fontes oficiais."),
    ], className="exec-dashboard page-dashboard")
