import re
import pandas as pd

from .loader import carregar_contratos


# Campos autorizados para saída das ferramentas.
# Não incluir contratados, fiscal_contrato,
# objeto, lembretes ou outros textos livres.
CAMPOS_PUBLICOS = (
    "id",
    "chave_contrato",
    "numero",
    "ano",
    "orgao",
    "tipo",
    "tipo_adt",
    "situacao",
    "valor",
    "data_firmatura",
    "inicio_vigencia",
    "fim_vigencia",
)


def _numero(valor):
    if pd.isna(valor):
        return None

    return round(float(valor), 2)


def _data(valor):
    if pd.isna(valor):
        return None

    return valor.strftime("%Y-%m-%d")


def _texto(valor):
    if pd.isna(valor):
        return None

    return str(valor)


def _registro(linha):
    return {
        "id": _texto(linha["id"]),
        "chave_contrato": _texto(
            linha["chave_contrato"]
        ),
        "numero": int(linha["numero"]),
        "ano": int(linha["ano"]),
        "orgao": _texto(linha["orgao"]),
        "tipo": _texto(linha["tipo"]),
        "tipo_adt": _texto(linha["tipo_adt"]),
        "situacao": _texto(linha["situacao"]),
        "valor": _numero(linha["valor"]),
        "data_firmatura": _data(
            linha["data_firmatura"]
        ),
        "inicio_vigencia": _data(
            linha["inicio_vigencia"]
        ),
        "fim_vigencia": _data(
            linha["fim_vigencia"]
        ),
    }


def _filtrar(
    ano=None,
    orgao=None,
    tipo=None,
    situacao=None,
):
    df = carregar_contratos()

    if ano is not None:
        df = df[df["ano"] == int(ano)]

    if orgao:
        df = df[
            df["orgao"].str.contains(
                str(orgao),
                case=False,
                na=False,
                regex=False,
            )
        ]

    if tipo:
        df = df[
            df["tipo"].str.casefold()
            == str(tipo).casefold()
        ]

    if situacao:
        df = df[
            df["situacao"].str.casefold()
            == str(situacao).casefold()
        ]

    return df


def consultar_contratos(
    ano: int = None,
    orgao: str = None,
    tipo: str = "Contrato",
    situacao: str = None,
    limite: int = 20,
):
    """
    Consulta contratos ou eventos contratuais.

    Por padrão, retorna somente contratos originais.
    Não expõe dados pessoais.
    """
    df = _filtrar(
        ano=ano,
        orgao=orgao,
        tipo=tipo,
        situacao=situacao,
    )

    limite = max(1, min(int(limite), 100))

    registros = [
        _registro(linha)
        for _, linha in df.head(limite).iterrows()
    ]

    return {
        "status": "ok",
        "total_encontrado": int(len(df)),
        "resultados_limitados": len(registros),
        "registros": registros,
    }


def resumir_contratos(ano: int):
    """
    Resumo dos contratos originais do exercício.

    Não soma aditivos ou distratos ao valor
    original dos contratos.
    """
    df = _filtrar(
        ano=ano,
        tipo="Contrato",
    )

    valores = df["valor"]

    return {
        "status": "ok",
        "ano": int(ano),
        "total_contratos": int(len(df)),
        "valor_total_original": _numero(
            valores.sum(min_count=1)
        ),
        "contratos_sem_valor": int(
            valores.isna().sum()
        ),
        "contratos_em_vigor": int(
            df["situacao"].eq("Em Vigor").sum()
        ),
        "contratos_encerrados": int(
            df["situacao"].eq("Encerrado").sum()
        ),
        "observacao": (
            "Os valores representam registros "
            "originais de contratos, não despesas "
            "efetivamente pagas nem valores "
            "contratuais atualizados por aditivos."
        ),
    }


def consultar_contrato_por_chave(
    chave_contrato: str,
):
    """
    Recupera contrato original e seus eventos.

    Exclui dados pessoais e textos livres.
    """
    df = carregar_contratos()

    chave = str(chave_contrato).strip()

    dados = df[
        df["chave_contrato"] == chave
    ].sort_values("data_firmatura")

    if dados.empty:
        return {
            "status": "nao_encontrado",
            "chave_contrato": chave,
            "registros": [],
        }

    registros = [
        _registro(linha)
        for _, linha in dados.iterrows()
    ]

    return {
        "status": "ok",
        "chave_contrato": chave,
        "total_registros": len(registros),
        "registros": registros,
        "observacao": (
            "O histórico contém contratos, "
            "aditivos e eventuais distratos. "
            "Os valores não devem ser somados "
            "automaticamente."
        ),
    }
