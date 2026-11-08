from pathlib import Path
from functools import lru_cache

import pandas as pd


RAIZ = Path(__file__).resolve().parents[3]

ARQUIVO = (
    RAIZ / "data" / "processed" / "gastos_diretos.csv"
)

CHAVE_EMPENHO = [
    "ano_referencia",
    "cod_unidade",
    "empenho"
]


@lru_cache(maxsize=1)
def carregar_despesas():
    return pd.read_csv(ARQUIVO, low_memory=False)


def rastrear_empenho(
    ano: int,
    codigo_unidade: int,
    numero_empenho: int
) -> dict:
    """
    Recupera os registros vinculados a um empenho.

    Não presume que valores repetidos representam
    novas movimentações contábeis.
    """

    df = carregar_despesas()

    dados = df.loc[
        (df["ano_referencia"] == ano)
        & (df["cod_unidade"] == codigo_unidade)
        & (df["empenho"] == numero_empenho)
    ].copy()

    if dados.empty:
        return {
            "status": "sem_dados",
            "ano": ano,
            "codigo_unidade": codigo_unidade,
            "numero_empenho": numero_empenho
        }

    valores_empenho = sorted(
        dados["valor_empenho"].dropna().unique().tolist()
    )

    liquidacoes = []

    for _, linha in dados.loc[
        dados["liquidacao"] != 0
    ].iterrows():
        liquidacoes.append({
            "id_origem": int(linha["id"]),
            "numero": int(linha["liquidacao"]),
            "data": (
                str(linha["data_liquidacao"])
                if pd.notna(linha["data_liquidacao"])
                else None
            ),
            "valor_registrado": float(linha["valor_liq"])
        })

    pagamentos = []

    for _, linha in dados.loc[
        (dados["numero_pagamento"] != 0)
        & dados["data_pagamento"].notna()
    ].iterrows():
        pagamentos.append({
            "id_origem": int(linha["id"]),
            "liquidacao": int(linha["liquidacao"]),
            "numero": int(linha["numero_pagamento"]),
            "data": str(linha["data_pagamento"]),
            "valor_registrado": float(linha["valor_pago"])
        })

    return {
        "status": "ok",
        "ano": ano,
        "codigo_unidade": codigo_unidade,
        "numero_empenho": numero_empenho,
        "valores_empenho_encontrados": [
            float(v) for v in valores_empenho
        ],
        "valor_empenho_consistente": (
            len(valores_empenho) == 1
        ),
        "quantidade_registros_origem": len(dados),
        "liquidacoes": liquidacoes,
        "pagamentos": pagamentos,
        "fonte": "gastos_diretos.csv",
        "validacao_contabil": "pendente"
    }

def consultar_execucao_empenho(
    ano: int,
    codigo_unidade: int,
    numero_empenho: int
) -> dict:

    df = carregar_despesas()

    dados = df.loc[
        (df["ano_referencia"] == ano)
        & (df["cod_unidade"] == codigo_unidade)
        & (df["empenho"] == numero_empenho)
    ].copy()

    if dados.empty:
        return {
            "status": "sem_dados",
            "mensagem": "Empenho não encontrado."
        }

    valores = dados["valor_empenho"].dropna().unique()

    if len(valores) != 1:
        return {
            "status": "inconsistente",
            "mensagem": "Valores divergentes para o empenho.",
            "valores_encontrados": valores.tolist()
        }

    valor_empenhado = float(valores[0])

    # Totais preliminares dos registros disponíveis.
    # Não equivalem necessariamente aos totais oficiais.
    total_liquidado = float(dados["valor_liq"].sum())
    total_pago = float(dados["valor_pago"].sum())

    # Anulações exigem validação da granularidade.
    registros_anulacao = int(
        (dados["valor_anulado"] != 0).sum()
    )


    diferenca = total_liquidado - valor_empenhado

    # Indicador preliminar de inconsistência.
    # Não considera ainda reforços, anulações ou
    # particularidades da fonte contábil.
    excedente = diferenca > 0.01

    status = (
        "inconsistente"
        if excedente
        else "preliminar"
    )

    return {
        "status": status,
        "ano": ano,
        "codigo_unidade": codigo_unidade,
        "numero_empenho": numero_empenho,
        "valor_empenhado": valor_empenhado,
        "liquidado_soma_linhas": total_liquidado,
        "pago_soma_linhas": total_pago,
        "diferenca_liquidacao_empenho": round(
            diferenca, 2
        ),
        "possivel_excesso_liquidacao": excedente,
        "registros_com_anulacao": registros_anulacao,
        "saldo_a_liquidar": None,
        "saldo_a_pagar": None,
        "restos_a_pagar": None,
        "observacao": (
            "Liquidações superiores ao valor empenhado; "
            "requer conciliação documental."
            if excedente
            else
            "Indicadores preliminares, sujeitos à "
            "validação das anulações e da fonte."
        )
    }

def consultar_execucao(
    ano: int,
    codigo_unidade: int | None = None
) -> dict:
    """
    Consulta agregada da execução orçamentária.

    Valores liquidados e pagos são preliminares.
    Não calcula saldos ou restos a pagar.
    """

    pasta = RAIZ / "data" / "processed" / "despesas"

    empenhos = pd.read_csv(
        pasta / "empenhos_consolidados.csv"
    )

    liquidacoes = pd.read_csv(
        pasta / "liquidacoes_consolidadas.csv"
    )

    pagamentos = pd.read_csv(
        pasta / "pagamentos_consolidados.csv"
    )

    origem = carregar_despesas()

    # Filtro por exercício
    empenhos = empenhos.loc[
        empenhos["ano_referencia"] == ano
    ].copy()

    liquidacoes = liquidacoes.loc[
        liquidacoes["ano_referencia"] == ano
    ].copy()

    pagamentos = pagamentos.loc[
        pagamentos["ano_referencia"] == ano
    ].copy()

    origem = origem.loc[
        origem["ano_referencia"] == ano
    ].copy()

    # Filtro opcional por unidade
    if codigo_unidade is not None:
        empenhos = empenhos.loc[
            empenhos["cod_unidade"] == codigo_unidade
        ]

        liquidacoes = liquidacoes.loc[
            liquidacoes["cod_unidade"] == codigo_unidade
        ]

        pagamentos = pagamentos.loc[
            pagamentos["cod_unidade"] == codigo_unidade
        ]

        origem = origem.loc[
            origem["cod_unidade"] == codigo_unidade
        ]

    if empenhos.empty:
        return {
            "status": "sem_dados",
            "ano": ano,
            "codigo_unidade": codigo_unidade,
            "mensagem": "Nenhum empenho encontrado."
        }

    # Empenhos com valores consistentes
    validos = empenhos.loc[
        empenhos["status"] == "consistente"
    ]

    total_empenhado = float(
        validos["valor_empenho"].sum()
    )

    # Somas exploratórias das movimentações
    total_liquidado = float(
        liquidacoes["valor_liq_soma_linhas"].sum()
    )

    total_pago = float(
        pagamentos["valor_pago_soma_linhas"].sum()
    )

    # Controle de qualidade
    divergentes = int(
        (empenhos["status"] != "consistente").sum()
    )

    pagamentos_repetidos = int(
        (pagamentos["status"] == "chave_repetida").sum()
    )

    # Eventos monetários fora dos filtros documentais
    liquidacoes_sem_numero = int(
        (
            (origem["liquidacao"] == 0)
            & (origem["valor_liq"] != 0)
        ).sum()
    )

    pagamentos_nao_incluidos = int(
        (
            (origem["valor_pago"] != 0)
            & (
                (origem["numero_pagamento"] == 0)
                | origem["data_pagamento"].isna()
            )
        ).sum()
    )
    
    
    diferenca_liquidacao = round(
        total_liquidado - total_empenhado, 2
    )

    excesso_aparente = diferenca_liquidacao > 0.01

    status = (
        "inconsistente"
        if excesso_aparente
        else "preliminar"
    )

    return {
        "status": status,
        "ano": ano,
        "codigo_unidade": codigo_unidade,
        "quantidade_empenhos": int(len(empenhos)),
        "quantidade_liquidacoes": int(len(liquidacoes)),
        "quantidade_pagamentos": int(len(pagamentos)),
        "valor_empenhado_identificado": round(
            total_empenhado, 2
        ),
        "valor_liquidado_soma_linhas": round(
            total_liquidado, 2
        ),
        "valor_pago_soma_linhas": round(
            total_pago, 2
        ),
        "diferenca_liquidacao_empenho": diferenca_liquidacao,
        "excesso_aparente_liquidacao": excesso_aparente,
        "empenhos_divergentes": divergentes,
        "chaves_pagamento_repetidas": pagamentos_repetidos,
        "liquidacoes_sem_numero_com_valor": (
            liquidacoes_sem_numero
        ),
        "pagamentos_com_valor_nao_incluidos": (
            pagamentos_nao_incluidos
        ),
        "saldo_a_liquidar": None,
        "saldo_a_pagar": None,
        "restos_a_pagar": None,
        "observacao": (
            "Consulta por exercício de referência do empenho. "
            "Os valores não foram integralmente reconciliados. "
            "O total empenhado exclui chaves divergentes; "
            "liquidações e pagamentos seguem os filtros "
            "documentais do consolidador. "
            "Não representa necessariamente o fluxo financeiro "
            "ocorrido no ano consultado."
        )
    }


