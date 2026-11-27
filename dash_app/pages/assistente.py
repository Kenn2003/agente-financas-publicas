"""Chat temporário com validação de privacidade antes do orquestrador."""
import re
import unicodedata

import dash
from dash import Input, Output, State, callback, ctx, dcc, html, no_update

from dash_app.components.base import cabecalho, nota, painel, rodape


dash.register_page(__name__, path="/assistente", name="Assistente", order=7)


def _normalizar(texto):
    decom = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(c for c in decom if not unicodedata.combining(c))


def validar_pergunta(pergunta):
    if not pergunta or not pergunta.strip():
        return "Digite uma pergunta para continuar."
    if len(pergunta) > 600:
        return "A pergunta deve ter no máximo 600 caracteres."
    termos = re.compile(r"\b(cpf|cnpj|matricula\w*|fornecedor\w*|contribuinte\w*|servidor\w*|nomes?|identifique|dados pessoais|linha a linha|individualizado)\b")
    identificadores = re.compile(r"(?<!\d)(?:\d{11,14}|\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})(?!\d)")
    if termos.search(_normalizar(pergunta)) or identificadores.search(pergunta):
        return "Por privacidade, o Assistente só atende consultas agregadas. Remova nomes, fornecedores, identificadores e pedidos sobre registros individuais."
    return None


def _mensagem(role, content, meta=None):
    user = role == "user"
    classe = "chat-message chat-user" if user else "chat-message chat-assistant"
    blocos = [html.Div("Você" if user else "Assistente", className="chat-author"), html.Div(content, className="chat-copy")]
    if meta:
        blocos.append(html.Div(meta, className="chat-meta"))
    return html.Article(blocos, className=classe)


def layout():
    return html.Div([
        cabecalho("Assistente", "Pergunte sobre totais e tendências de receitas, despesas, licitações, contratos e dívida ativa."),
        html.Div([html.Span("CONSULTA SOB DEMANDA", className="exec-badge"), html.Span("Ao enviar uma pergunta válida, o texto é encaminhado ao Gemini e aos agentes locais para gerar uma resposta agregada." )], className="exec-status"),
        painel("Conversa", "O histórico fica apenas na memória desta página; limpar ou recarregar remove a conversa.", html.Div([
            dcc.Store(id="assist-historico", data=[], storage_type="memory"),
            dcc.Loading(html.Div(id="assist-transcript", children=html.Div("Faça uma pergunta agregada para começar.", className="chat-empty"), className="chat-transcript", role="log", **{"aria-live": "polite"}), type="circle", color="#C5E86C"),
            html.Div([
                html.Label("Sua pergunta", htmlFor="assist-pergunta", className="chat-author"),
                dcc.Textarea(id="assist-pergunta", placeholder="Ex.: Como evoluíram as receitas nos exercícios disponíveis?", maxLength=600, className="chat-input"),
                html.Div([html.Span("Não inclua dados pessoais ou pedidos sobre registros individuais.", className="chat-hint"), html.Div([html.Button("Limpar", id="assist-limpar", n_clicks=0, className="page-button page-button-quiet"), html.Button("Enviar pergunta", id="assist-enviar", n_clicks=0, className="page-button", type="button")], className="chat-actions")], className="chat-compose-footer"),
                html.Div(id="assist-feedback", className="exec-inline-note", role="status"),
            ], className="chat-compose"),
        ], className="chat-shell")),
        painel("Privacidade e limites", "Controles herdados do Assistente Streamlit do projeto.", html.Div([
            html.Div([html.Strong("Filtro local antes do envio"), html.P("Perguntas com identificadores, nomes, fornecedores e pedidos individualizados são recusadas antes de chamar o modelo." )], className="page-explainer"),
            html.Div([html.Strong("Resposta exploratória"), html.P("Respostas de IA podem conter erros. Confirme critérios e valores nas bases e documentos oficiais." )], className="page-explainer"),
        ], className="page-explainer-grid")),
        nota("A pergunta válida é enviada ao provedor Gemini. Não envie informações pessoais, sigilosas ou que não devam sair do ambiente local."),
        rodape("A interface não persiste conversa no servidor e cria o orquestrador por solicitação para não compartilhar histórico de modelo entre sessões."),
    ], className="exec-dashboard page-dashboard")


@callback(Output("assist-historico", "data"), Output("assist-transcript", "children"), Output("assist-pergunta", "value"), Output("assist-feedback", "children"), Input("assist-enviar", "n_clicks"), Input("assist-limpar", "n_clicks"), State("assist-pergunta", "value"), State("assist-historico", "data"), prevent_initial_call=True)
def conversar(enviar, limpar, pergunta, historico):
    historico = list(historico or [])
    if ctx.triggered_id == "assist-limpar":
        return [], html.Div("Faça uma pergunta agregada para começar.", className="chat-empty"), "", "Conversa limpa desta sessão."
    mensagem = validar_pergunta(pergunta or "")
    if mensagem:
        return historico, no_update, pergunta, "A pergunta não foi enviada ao provedor."

    historico.append({"role": "user", "content": pergunta.strip()})
    try:
        from src.agents.orchestrador import Orquestrador
        resultado = Orquestrador().executar(pergunta.strip())
        if not isinstance(resultado, dict):
            raise TypeError("formato inesperado")
        resposta = str(resultado.get("resposta") or "Não foi possível obter uma resposta.")
        status = str(resultado.get("status", "erro_execucao"))
        tarefas = resultado.get("agentes_acionados", [])
        agentes = [t.get("agente") if isinstance(t, dict) else str(t) for t in tarefas]
        rotulos = {"receitas": "Receitas", "despesas": "Despesas", "licitacoes": "Licitações", "contratos": "Contratos", "divida_ativa": "Dívida ativa"}
        meta = "Agentes consultados: " + ", ".join(rotulos.get(a, a) for a in agentes) if agentes else ""
        if status == "parcial":
            meta = (meta + " · Resposta parcial; um ou mais agentes não concluíram.").strip(" ·")
    except Exception:
        status = "erro_execucao"
        resposta = "Não consegui consultar os agentes agora. Verifique a configuração local do Gemini e tente novamente."
        meta = ""

    historico.append({"role": "assistant", "content": resposta, "status": status, "meta": meta})
    conteudo = [_mensagem(item["role"], item["content"], item.get("meta")) for item in historico]
    return historico, conteudo, "", "Consulta concluída." if status not in {"erro_execucao", "erro_roteamento"} else "O serviço não concluiu a consulta."
