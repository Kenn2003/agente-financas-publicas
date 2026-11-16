from datetime import date
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


@st.cache_data(show_spinner=False)
def carregar_base():
    from src.agents.divida_ativa.loader import carregar_divida_ativa

    df = carregar_divida_ativa()
    if df is None or df.empty:
        raise ValueError("A base de inscrições está vazia.")

    dados = df[["valor_divida", "data_inscricao", "ano", "mes"]].copy()
    dados["valor_divida"] = pd.to_numeric(dados["valor_divida"], errors="coerce")
    dados["data_inscricao"] = pd.to_datetime(
        dados["data_inscricao"], errors="coerce"
    )
    dados["ano"] = pd.to_numeric(dados["ano"], errors="coerce")
    dados["mes"] = pd.to_numeric(dados["mes"], errors="coerce")
    dados = dados.dropna(subset=["valor_divida", "data_inscricao"])
    return dados.loc[dados["valor_divida"] >= 0].copy()


@st.cache_resource(show_spinner=False)
def carregar_modelos():
    import joblib

    pasta = RAIZ / "models"
    caminhos = {
        "inadimplencia": pasta / "inadimplencia.joblib",
        "recuperabilidade": pasta / "recuperabilidade.joblib",
    }
    ausentes = [str(p.name) for p in caminhos.values() if not p.is_file()]
    if ausentes:
        raise FileNotFoundError(", ".join(ausentes))

    pacotes = {nome: joblib.load(caminho) for nome, caminho in caminhos.items()}
    for nome, pacote in pacotes.items():
        if not isinstance(pacote, dict) or "estimator" not in pacote:
            raise ValueError(f"Artefato inválido: {nome}")
    return pacotes


def moeda_brl(valor):
    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def montar_features(pacote, valor_divida, data_inscricao):
    import numpy as np

    referencia = pd.Timestamp(pacote["data_referencia"])
    idade = max(0, (referencia - pd.Timestamp(data_inscricao)).days)
    valores = {
        "log_valor_divida": np.log1p(valor_divida),
        "idade_divida_dias": idade,
    }
    colunas = pacote.get("features", ["log_valor_divida", "idade_divida_dias"])
    desconhecidas = [coluna for coluna in colunas if coluna not in valores]
    if desconhecidas:
        raise ValueError("O artefato contém variáveis não reconhecidas.")
    return pd.DataFrame([[valores[coluna] for coluna in colunas]], columns=colunas)


st.title("Demonstração de inadimplência — dados sintéticos")
st.warning(
    "Demonstração acadêmica. Os alvos dos modelos são proxies sintéticos, "
    "não resultados observados de pagamento, inadimplência ou recuperação. "
    "Os scores não são previsões reais e não devem orientar cobrança ou "
    "decisões sobre contribuintes."
)
st.caption(
    "A interface não exibe nomes, identificadores ou linhas individuais. "
    "Os indicadores da base são agregados; o simulador aceita apenas valor e data."
)

try:
    base = carregar_base()
except Exception:
    st.error(
        "Não foi possível carregar a base agregada de dívida ativa. "
        "Confira a configuração local e os arquivos de dados do projeto."
    )
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Inscrições na base", f"{len(base):,}".replace(",", "."))
c2.metric("Valor registrado (soma)", moeda_brl(base["valor_divida"].sum()))
c3.metric(
    "Mediana dos valores registrados",
    moeda_brl(base["valor_divida"].median()),
)

mensal = (
    base.assign(periodo=base["data_inscricao"].dt.to_period("M").dt.to_timestamp())
    .groupby("periodo", as_index=False)
    .agg(registros=("valor_divida", "size"), valor_registrado=("valor_divida", "sum"))
    .sort_values("periodo")
)
if not mensal.empty:
    grafico = px.bar(
        mensal,
        x="periodo",
        y="registros",
        title="Inscrições registradas por mês",
        labels={"periodo": "Mês de inscrição", "registros": "Registros"},
        hover_data={"valor_registrado": ":,.2f"},
    )
    st.plotly_chart(grafico, use_container_width=True)
    st.caption(
        "Contagens da base disponível; não representam pagamentos, "
        "recuperação ou inadimplência observada."
    )

st.subheader("Simulador do modelo demonstrativo")
st.write(
    "Informe um valor e uma data para obter a saída dos modelos treinados "
    "com rótulos sintéticos. Os resultados variam conforme os artefatos locais."
)

try:
    modelos = carregar_modelos()
except ModuleNotFoundError as erro:
    if erro.name in {"joblib", "sklearn", "scikit_learn"} or (erro.name or "").startswith("sklearn"):
        st.info(
            "Para carregar os modelos neste ambiente, instale as dependências "
            "já documentadas pelo projeto (`scikit-learn` e `joblib`) e reinicie "
            "o Streamlit. Nenhuma instalação foi iniciada pela tela."
        )
    else:
        st.error("Não foi possível carregar as dependências dos modelos.")
    st.stop()
except FileNotFoundError:
    st.warning(
        "Os artefatos `.joblib` esperados não foram encontrados em `models/`. "
        "A visualização agregada continua disponível."
    )
    st.stop()
except Exception as erro:
    st.error(
        "Não foi possível carregar os modelos. Confira os artefatos locais "
        f"({type(erro).__name__})."
    )
    st.stop()

pacote_inadimplencia = modelos["inadimplencia"]
data_referencia = pd.Timestamp(pacote_inadimplencia["data_referencia"]).date()
valor_padrao = float(base["valor_divida"].median())
data_padrao = min(
    max(base["data_inscricao"].median().date(), base["data_inscricao"].min().date()),
    data_referencia,
)

with st.form("simulacao_inadimplencia"):
    col_valor, col_data = st.columns(2)
    valor = col_valor.number_input(
        "Valor registrado (R$)",
        min_value=0.01,
        value=max(0.01, valor_padrao),
        step=100.0,
        format="%.2f",
    )
    data = col_data.date_input(
        "Data de inscrição",
        value=data_padrao,
        min_value=date(1900, 1, 1),
        max_value=data_referencia,
        format="DD/MM/YYYY",
    )
    executar = st.form_submit_button("Executar demonstração")

if executar:
    try:
        entrada = montar_features(pacote_inadimplencia, valor, data)
        estimador = pacote_inadimplencia["estimator"]
        classes = list(estimador.classes_)
        probabilidades = estimador.predict_proba(entrada)[0]
        if 1 not in classes:
            raise ValueError("O modelo não contém a classe sintética positiva 1.")
        prob_proxy = float(probabilidades[classes.index(1)])

        st.metric("Score sintético de inadimplência", f"{prob_proxy:.1%}")
        st.caption(
            "Probabilidade associada à classe sintética 1 no modelo; "
            "não é probabilidade real de inadimplência."
        )

        pacote_recuperabilidade = modelos["recuperabilidade"]
        entrada_recuperabilidade = montar_features(
            pacote_recuperabilidade, valor, data
        )
        modelo_recuperabilidade = pacote_recuperabilidade["estimator"]
        probabilidades_rec = modelo_recuperabilidade.predict_proba(
            entrada_recuperabilidade
        )[0]
        classes_rec = list(modelo_recuperabilidade.classes_)
        resultados = pd.DataFrame(
            {
                "Faixa sintética": [str(classe) for classe in classes_rec],
                "Score do modelo": [float(p) for p in probabilidades_rec],
            }
        ).sort_values("Score do modelo", ascending=False)
        st.dataframe(
            resultados.style.format({"Score do modelo": "{:.1%}"}),
            hide_index=True,
            use_container_width=True,
        )
        st.caption(
            "As faixas de recuperabilidade também são sintéticas; não indicam "
            "recuperação efetiva ou saldo atualizado."
        )
    except Exception as erro:
        st.error(
            "A simulação não foi concluída. Confira se os artefatos usam as "
            f"features documentadas ({type(erro).__name__})."
        )
