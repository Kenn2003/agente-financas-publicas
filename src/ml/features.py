
from pathlib import Path

import numpy as np
import pandas as pd


# Caminho da raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parents[2]

# Arquivo original da dívida ativa
ARQUIVO_DIVIDA = RAIZ_PROJETO / "relatorio_dívida_ativa.csv"


def converter_valor(valor):
    """
    Converte valores monetários para números decimais.
    Aceita valores como 1.234,56 ou 1234.56.
    """
    if pd.isna(valor):
        return np.nan

    if isinstance(valor, (int, float, np.number)):
        return float(valor)

    valor = str(valor).strip()
    valor = valor.replace("R$", "").replace(" ", "")

    if "," in valor:
        valor = valor.replace(".", "")
        valor = valor.replace(",", ".")

    try:
        return float(valor)
    except ValueError:
        return np.nan


def carregar_base_divida(caminho=ARQUIVO_DIVIDA):
    """
    Carrega a base original de dívida ativa.
    """
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig"
    )

    colunas_necessarias = [
        "Valor Total da Dívida",
        "Data da Inscrição"
    ]

    for coluna in colunas_necessarias:
        if coluna not in df.columns:
            raise ValueError(
                f"Coluna obrigatória não encontrada: {coluna}"
            )

    return df


def construir_features(df):
    """
    Constrói variáveis preditoras a partir da dívida ativa.

    Não utiliza nome ou CPF/CNPJ como variável preditora.
    Não cria rótulos artificiais de inadimplência ou recuperação.
    """

    base = df.copy()

    # Padronização dos campos necessários
    base["valor_divida"] = (
        base["Valor Total da Dívida"]
        .apply(converter_valor)
    )

    base["data_inscricao"] = pd.to_datetime(
        base["Data da Inscrição"],
        dayfirst=True,
        errors="coerce"
    )

    # Remoção de registros sem informações essenciais
    base = base.dropna(
        subset=["valor_divida", "data_inscricao"]
    )

    # Mantém apenas valores de dívida não negativos
    base = base[base["valor_divida"] >= 0].copy()

    # Variáveis temporais
    base["ano_inscricao"] = (
        base["data_inscricao"].dt.year
    )

    base["mes_inscricao"] = (
        base["data_inscricao"].dt.month
    )

    base["trimestre_inscricao"] = (
        base["data_inscricao"].dt.quarter
    )

    base["dia_semana_inscricao"] = (
        base["data_inscricao"].dt.dayofweek
    )

    # Transformação para reduzir a assimetria dos valores
    base["log_valor_divida"] = np.log1p(
        base["valor_divida"]
    )

    # Classificação do valor em faixas
    base["faixa_valor"] = pd.cut(
        base["valor_divida"],
        bins=[-0.01, 500, 1000, 5000, 10000, np.inf],
        labels=[
            "Muito baixa",
            "Baixa",
            "Média",
            "Alta",
            "Muito alta"
        ]
    )

    # Colunas que serão utilizadas pelos próximos módulos
    colunas_features = [
        "data_inscricao",
        "valor_divida",
        "log_valor_divida",
        "ano_inscricao",
        "mes_inscricao",
        "trimestre_inscricao",
        "dia_semana_inscricao",
        "faixa_valor"
    ]

    return base[colunas_features].reset_index(drop=True)


def adicionar_alvos_sinteticos(df, semente=42):
    """
    Cria alvos sintéticos para demonstrar o pipeline de ML.

    ATENÇÃO:
    Os alvos são simulados e não representam pagamentos,
    inadimplência ou recuperação reais dos contribuintes.

    A regra utiliza valor da dívida e tempo desde a inscrição.
    """

    base = df.copy()

    data_referencia = base["data_inscricao"].max()

    base["dias_desde_inscricao"] = (
        data_referencia - base["data_inscricao"]
    ).dt.days

    # Probabilidade simulada de inadimplência
    
    logit = -2.5 + 0.15 * base["log_valor_divida"]

    probabilidade = 1 / (1 + np.exp(-logit))

    gerador = np.random.default_rng(semente)

    base["inadimplente_sintetico"] = (
        gerador.binomial(1, probabilidade)
    )

    # Taxa de recuperação simulada
    fator_valor = 1 / (
        1 + np.exp(
            base["log_valor_divida"] - 7
        )
    )

    fator_tempo = np.exp(
        -base["dias_desde_inscricao"] / 365
    )

    taxa_base = (
        0.15
        + 0.65 * fator_valor
        + 0.15 * fator_tempo
    )

    ruido = gerador.normal(0, 0.08, len(base))

    base["taxa_recuperacao_sintetica"] = np.clip(
        taxa_base + ruido,
        0,
        1
    )

    return base



if __name__ == "__main__":

    dados = carregar_base_divida()
    features = construir_features(dados)
    dados_sinteticos = adicionar_alvos_sinteticos(features)

    print("\nDistribuição do alvo sintético:")
    print(
        dados_sinteticos[
            "inadimplente_sintetico"
        ].value_counts(normalize=True)
    )

    print("\nTaxa média de recuperação sintética:")
    print(
        dados_sinteticos[
            "taxa_recuperacao_sintetica"
        ].mean()
    )


    print("Base original:", len(dados), "registros")
    print("Base após tratamento:", len(features), "registros")
    print("\nVariáveis construídas:")
    print(features.columns.tolist())

    print("\nResumo estatístico:")
    print(features.describe(include="all"))
