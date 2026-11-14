import re
import sys
import unicodedata
from pathlib import Path

import streamlit as st


RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


@st.cache_resource(show_spinner=False)
def carregar_orquestrador():
    from src.agents.orchestrador import Orquestrador

    return Orquestrador()


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(caractere for caractere in texto if not unicodedata.combining(caractere))


def validar_pergunta(pergunta):
    if not pergunta or not pergunta.strip():
        return "Digite uma pergunta para continuar."
    if len(pergunta) > 600:
        return "A pergunta deve ter no máximo 600 caracteres."

    normalizada = normalizar(pergunta)
    termos_individuais = re.compile(
        r"\b(cpf|cnpj|matricula\w*|fornecedor\w*|contribuinte\w*|servidor\w*|"
        r"nomes?|identifique|dados pessoais|linha a linha|individualizado)\b"
    )
    identificador_numerico = re.compile(r"(?<!\d)(?:\d{11,14}|\d{3}\.\d{3}\.\d{3}-\d{2}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})(?!\d)")
    if termos_individuais.search(normalizada) or identificador_numerico.search(pergunta):
        return (
            "Por privacidade, o Assistente só atende consultas agregadas. "
            "Remova nomes, fornecedores, identificadores e pedidos sobre registros individuais."
        )
    return None


def nome_agente(nome):
    rotulos = {
        "receitas": "Receitas",
        "despesas": "Despesas",
        "licitacoes": "Licitações",
        "contratos": "Contratos",
        "divida_ativa": "Dívida ativa",
    }
    return rotulos.get(nome, nome.replace("_", " ").title())


def iniciar_historico():
    if "historico_assistente" not in st.session_state:
        st.session_state.historico_assistente = []


st.title("Assistente de Finanças Públicas")
st.caption(
    "Faça perguntas em linguagem natural sobre receitas, despesas, licitações, "
    "contratos e dívida ativa. O Gemini encaminha a consulta aos agentes especializados."
)
st.info(
    "Use perguntas agregadas. Não inclua nomes, CPFs/CNPJs, matrículas, "
    "fornecedores ou pedidos sobre registros individuais. O histórico fica "
    "somente nesta sessão e não é salvo pela interface."
)

iniciar_historico()

col_titulo, col_limpar = st.columns([5, 1])
with col_limpar:
    if st.button("Limpar conversa", width="stretch"):
        st.session_state.historico_assistente = []
        st.rerun()

for item in st.session_state.historico_assistente:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
        if item["role"] == "assistant" and item.get("agentes"):
            labels = ", ".join(nome_agente(nome) for nome in item["agentes"])
            st.caption(f"Agentes consultados: {labels}")
        if item["role"] == "assistant" and item.get("status") == "parcial":
            st.caption("A resposta foi parcial; um ou mais agentes não concluíram a consulta.")

pergunta = st.chat_input("Ex.: Como evoluíram as receitas de 2021 a 2025?")
if pergunta:
    st.session_state.historico_assistente.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    mensagem_validacao = validar_pergunta(pergunta)
    if mensagem_validacao:
        resposta = mensagem_validacao
        status = "entrada_invalida"
        agentes = []
    else:
        try:
            with st.spinner("Analisando a pergunta e consultando os agentes..."):
                orquestrador = carregar_orquestrador()
                resultado = orquestrador.executar(pergunta)
            if not isinstance(resultado, dict):
                raise TypeError("Formato de resposta inesperado")
            resposta = str(resultado.get("resposta") or "Não foi possível obter uma resposta.")
            status = str(resultado.get("status", "erro_execucao"))
            tarefas = resultado.get("agentes_acionados", [])
            agentes = [
                tarefa.get("agente") if isinstance(tarefa, dict) else str(tarefa)
                for tarefa in tarefas
            ]
        except Exception as erro:
            # A mensagem técnica fica fora da interface para não expor segredos ou detalhes internos.
            status = "erro_execucao"
            resposta = (
                "Não consegui consultar os agentes agora. Verifique se a chave do Gemini "
                "está configurada no ambiente local e tente novamente."
            )
            agentes = []

    st.session_state.historico_assistente.append(
        {"role": "assistant", "content": resposta, "status": status, "agentes": agentes}
    )
    with st.chat_message("assistant"):
        st.markdown(resposta)
        if agentes:
            st.caption("Agentes consultados: " + ", ".join(nome_agente(nome) for nome in agentes))
        if status == "parcial":
            st.caption("A resposta foi parcial; um ou mais agentes não concluíram a consulta.")
        elif status == "fora_escopo":
            st.caption("Pergunta fora do escopo dos agentes disponíveis.")
