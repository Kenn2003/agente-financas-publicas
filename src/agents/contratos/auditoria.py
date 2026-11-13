import pandas as pd

from .loader import carregar_contratos


def _valor(valor):
    if pd.isna(valor):
        return None
    return round(float(valor), 2)


def analisar_aditivos(ano: int):
    """
    Analisa os aditivos associados aos contratos
    originais do ano informado.

    Não interpreta a soma dos aditivos como
    acréscimo contratual líquido.
    """
    df = carregar_contratos()

    chaves = set(
        df.loc[
            (df["tipo"] == "Contrato")
            & (df["ano"] == int(ano)),
            "chave_contrato",
        ]
    )

    aditivos = df[
        (df["tipo"] == "Aditivo")
        & df["chave_contrato"].isin(chaves)
    ]

    valores = aditivos["valor"]

    return {
        "status": "ok",
        "ano_contrato_original": int(ano),
        "total_aditivos": int(len(aditivos)),
        "contratos_com_aditivos": int(
            aditivos["chave_contrato"].nunique()
        ),
        "aditivos_com_valor": int(
            valores.notna().sum()
        ),
        "aditivos_sem_valor": int(
            valores.isna().sum()
        ),
        "soma_valores_informados": _valor(
            valores.sum(min_count=1)
        ),
        "observacao": (
            "A soma representa os valores informados "
            "nos registros de aditivos. Não corresponde "
            "necessariamente ao acréscimo líquido nem "
            "ao valor atualizado dos contratos."
        ),
    }


def analisar_vigencias(
    ano: int,
    data_referencia: str = None,
):
    """
    Analisa a vigência dos contratos originais
    na data de referência.

    Utiliza a data de término mais recente
    entre os registros vinculados, como
    indicador preliminar.
    """
    df = carregar_contratos()

    referencia = (
        pd.Timestamp(data_referencia)
        if data_referencia
        else pd.Timestamp.today().normalize()
    )

    originais = df[
        (df["tipo"] == "Contrato")
        & (df["ano"] == int(ano))
    ].copy()

    eventos = df[
        df["chave_contrato"].isin(
            originais["chave_contrato"]
        )
    ]

    ultimos_fins = eventos.groupby(
        "chave_contrato"
    )["fim_vigencia"].max()

    originais["fim_considerado"] = (
        originais["chave_contrato"].map(ultimos_fins)
    )

    encerrados_prazo = (
        originais["fim_considerado"] < referencia
    )

    futuros = (
        originais["fim_considerado"] >= referencia
    )

    atipicos = (
        originais["fim_considerado"].dt.year > 2100
    )

    return {
        "status": "ok",
        "ano_contrato_original": int(ano),
        "data_referencia": referencia.strftime(
            "%Y-%m-%d"
        ),
        "total_contratos": int(len(originais)),
        "termino_anterior_referencia": int(
            encerrados_prazo.sum()
        ),
        "termino_na_referencia_ou_posterior": int(
            futuros.sum()
        ),
        "vigencias_atipicas_apos_2100": int(
            atipicos.sum()
        ),
        "observacao": (
            "Indicadores baseados nas datas registradas. "
            "A data máxima entre os eventos não comprova "
            "vigência jurídica atual. Distratos, rescisões "
            "e alterações contratuais exigem análise "
            "documental."
        ),
    }


def auditar_contratos(
    ano: int,
    limite: int = 20,
):
    """
    Detecta inconsistências cadastrais e
    temporais sem expor dados pessoais.
    """
    df = carregar_contratos()

    dados = df[df["ano"] == int(ano)].copy()

    limite = max(1, min(int(limite), 100))

    alertas = []

    for _, linha in dados.iterrows():
        motivos = []

        if (
            pd.notna(linha["inicio_vigencia"])
            and pd.notna(linha["fim_vigencia"])
            and linha["fim_vigencia"]
            < linha["inicio_vigencia"]
        ):
            motivos.append(
                "Fim da vigência anterior ao início."
            )

        if (
            pd.notna(linha["fim_vigencia"])
            and linha["fim_vigencia"].year > 2100
        ):
            motivos.append(
                "Data de término após o ano 2100."
            )

        if (
            linha["tipo"] == "Contrato"
            and pd.isna(linha["valor"])
        ):
            motivos.append(
                "Contrato original sem valor."
            )

        if motivos:
            alertas.append({
                "id": str(linha["id"]),
                "chave_contrato": str(
                    linha["chave_contrato"]
                ),
                "tipo": str(linha["tipo"]),
                "motivos": motivos,
            })

    return {
        "status": "ok",
        "ano": int(ano),
        "registros_analisados": int(len(dados)),
        "total_registros_com_alerta": len(alertas),
        "alertas": alertas[:limite],
        "resultados_limitados": min(
            len(alertas), limite
        ),
        "observacao": (
            "Alertas preliminares de qualidade "
            "cadastral. Não constituem prova "
            "de irregularidade administrativa."
        ),
    }
