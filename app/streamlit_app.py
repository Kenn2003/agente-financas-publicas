import streamlit as st

st.set_page_config(
    page_title="Finanças Públicas de Palmas",
    page_icon="📊",
    layout="wide",
)

pagina = st.navigation([
    st.Page("pages/dashboard.py", title="Dashboard", default=True),
    st.Page("pages/assistente.py", title="Assistente"),
    st.Page("pages/inadimplencia.py", title="Inadimplência — demonstração"),
])
pagina.run()
