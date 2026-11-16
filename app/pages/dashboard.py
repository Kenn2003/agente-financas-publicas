from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st


RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}



CODIGOS_TOTAL = {
    "1.0.0.0.00.0.0",
    "2.0.0.0.00.0.0",
    "7.0.0.0.00.0.0",
    "8.0.0.0.00.0.0",
}

def moeda_brl(valor):
    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data
def carregar_receitas():
    arquivo = RAIZ / "data/ready/receitas_recentes.parquet"
    df = pd.read_parquet(
        arquivo,
        columns=["ano", "mes", "codigo", "valor_arrecado_mes"],
    )
    df["codigo"] = df["codigo"].astype("string").str.strip()

    for coluna in ["ano", "mes", "valor_arrecado_mes"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df = df[df["codigo"].isin(CODIGOS_TOTAL)].copy()

    return df.dropna(
        subset=["ano", "mes", "valor_arrecado_mes"]
    ).assign(
        ano=lambda dados: dados["ano"].astype(int),
        mes=lambda dados: dados["mes"].astype(int),
    )


@st.cache_data
def carregar_despesas():
    arquivo = RAIZ / "data/ready/gastos_diretos.parquet"
    df = pd.read_parquet(
        arquivo,
        columns=["ano_referencia", "valor_empenho", "valor_liq", "valor_pago"],
    )
    df["ano_referencia"] = pd.to_numeric(df["ano_referencia"], errors="coerce")
    for coluna in ["valor_empenho", "valor_liq", "valor_pago"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df.dropna(subset=["ano_referencia"]).assign(
        ano_referencia=lambda dados: dados["ano_referencia"].astype(int)
    )


st.title("Finanças Públicas de Palmas")
st.caption("Painel exploratório baseado nos arquivos Parquet disponíveis.")

try:
    receitas = carregar_receitas()
    despesas = carregar_despesas()
except Exception:
    st.error("Não foi possível carregar os dados. Confira os arquivos Parquet em data/ready.")
    st.stop()

aba_receitas, aba_despesas = st.tabs(["Receitas", "Despesas"])

with aba_receitas:
    st.subheader("Receitas recentes")
    anos_receita = sorted(receitas["ano"].unique().tolist())
    ano_receita = st.selectbox(
        "Exercício", anos_receita, index=len(anos_receita) - 1, key="ano_receitas"
    )
    dados_ano = receitas.loc[receitas["ano"] == ano_receita]
    mensal_completo = (
        dados_ano.groupby("mes", as_index=False)["valor_arrecado_mes"].sum()
        .sort_values("mes")
    )
    meses_presentes = sorted(mensal_completo["mes"].tolist())
    meses_selecionados = st.multiselect(
        "Filtrar meses", meses_presentes,
        default=meses_presentes,
        format_func=lambda mes: MESES.get(mes, str(mes)),
        key="meses_receitas",
    )
    mensal = mensal_completo.loc[mensal_completo["mes"].isin(meses_selecionados)].copy()
    total_ano = mensal["valor_arrecado_mes"].sum()

    col1, col2 = st.columns(2)
    col1.metric("oma dos códigos de 1º nível no período", moeda_brl(total_ano))
    col2.metric("Meses incluídos", f"{len(meses_selecionados)} de {len(meses_presentes)}")
    if ano_receita == max(anos_receita) and len(meses_presentes) < 12:
        st.warning(
            f"{ano_receita} tem registros em {len(meses_presentes)} meses; "
            "a soma anual pode estar incompleta."
        )
    if mensal.empty:
        st.info("Selecione pelo menos um mês para exibir os dados.")
    else:
        mensal["Mês"] = mensal["mes"].map(MESES)
        grafico = px.bar(
            mensal, x="Mês", y="valor_arrecado_mes",
            title=f"Valores mensais registrados — {ano_receita}",
            labels={"valor_arrecado_mes": "Soma registrada (R$)"},
        )
        grafico.update_layout(showlegend=False)
        st.plotly_chart(grafico, width="stretch")
        tabela = mensal[["Mês", "valor_arrecado_mes"]].rename(
            columns={"valor_arrecado_mes": "Soma registrada (R$)"}
        )
        st.dataframe(tabela, hide_index=True, width="stretch")
        st.download_button(
            "Baixar resumo mensal (CSV)",
            data=tabela.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"receitas_mensais_{ano_receita}.csv",
            mime="text/csv",
        )
    meses_exibidos = ", ".join(
        MESES[mes] for mes in meses_selecionados
    ) or "nenhum"

    st.caption(
        f"Período exibido: {meses_exibidos} de {ano_receita}. "
        "Critério: soma de valor_arrecado_mes para os códigos de primeiro nível "
        "definidos pelo Assistente e presentes na base. Medida exploratória; "
        "validação oficial pendente."
    )

with aba_despesas:
    st.subheader("Despesas — execução registrada")
    anos_despesa = sorted(despesas["ano_referencia"].unique().tolist())
    ano_despesa = st.selectbox(
        "Exercício de referência", anos_despesa,
        index=len(anos_despesa) - 1, key="ano_despesas",
    )
    dados_ano = despesas.loc[despesas["ano_referencia"] == ano_despesa]
    c1, c2, c3 = st.columns(3)
    c1.metric("Empenhado — soma registrada", moeda_brl(dados_ano["valor_empenho"].sum()))
    c2.metric("Liquidado — soma registrada", moeda_brl(dados_ano["valor_liq"].sum()))
    c3.metric("Pago — soma registrada", moeda_brl(dados_ano["valor_pago"].sum()))

    anual = (
        despesas.groupby("ano_referencia", as_index=False)[
            ["valor_empenho", "valor_liq", "valor_pago"]
        ].sum().sort_values("ano_referencia")
    )
    longo = anual.melt(
        id_vars="ano_referencia", var_name="Etapa", value_name="Soma registrada (R$)"
    )
    nomes = {"valor_empenho": "Empenhado", "valor_liq": "Liquidado", "valor_pago": "Pago"}
    longo["Etapa"] = longo["Etapa"].map(nomes)
    grafico = px.line(
        longo, x="ano_referencia", y="Soma registrada (R$)", color="Etapa",
        markers=True, title="Somas anuais por etapa — séries separadas",
        labels={"ano_referencia": "Exercício"},
    )
    st.plotly_chart(grafico, width="stretch")

    resumo_ano = pd.DataFrame([{
        "Exercício": ano_despesa,
        "Empenhado (R$)": dados_ano["valor_empenho"].sum(),
        "Liquidado (R$)": dados_ano["valor_liq"].sum(),
        "Pago (R$)": dados_ano["valor_pago"].sum(),
    }])
    st.dataframe(resumo_ano, hide_index=True, width="stretch")
    st.download_button(
        "Baixar resumo de despesas do exercício (CSV)",
        data=resumo_ano.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"despesas_resumo_{ano_despesa}.csv",
        mime="text/csv",
    )
    st.download_button(
        "Baixar série anual agregada (CSV)",
        data=anual.rename(columns={"ano_referencia": "Exercício"})
        .to_csv(index=False).encode("utf-8-sig"),
        file_name="despesas_serie_anual.csv",
        mime="text/csv",
    )

    negativos = {
        coluna: int((dados_ano[coluna] < 0).sum())
        for coluna in ["valor_empenho", "valor_liq", "valor_pago"]
    }
    st.caption(
        f"Registros negativos no exercício — empenhado: {negativos['valor_empenho']}; "
        f"liquidado: {negativos['valor_liq']}; pago: {negativos['valor_pago']}."
    )
    st.warning(
        "Somas diretas dos registros; valores negativos foram preservados. "
        "A fonte é preliminar e não deve ser interpretada como saldo orçamentário "
        "conciliado nem comparada diretamente às receitas."
    )
