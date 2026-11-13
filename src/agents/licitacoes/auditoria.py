import pandas as pd

from src.agents.licitacoes.loader import carregar_licitacoes


def auditar_valores_licitacoes(
    ano: int,
    limite: int = 20,
) -> dict:
    """
    Identifica licitações com valor homologado
    superior ao estimado.

    Os resultados são alertas preliminares,
    não conclusões de irregularidade.
    """
    if limite < 1:
        raise ValueError("limite deve ser positivo")

    df = carregar_licitacoes()
    df = df.loc[df["ano"] == ano].copy()

    if df.empty:
        return {"status": "sem_dados", "ano": ano}

    # Somente registros com os dois valores disponíveis.
    comparaveis = df.dropna(
        subset=["valor_estimado", "valor_homologado"]
    ).copy()

    # Valor estimado zero não permite calcular
    # percentual de diferença.
    comparaveis = comparaveis[
        comparaveis["valor_estimado"] > 0
    ].copy()

    comparaveis["diferenca"] = (
        comparaveis["valor_homologado"]
        - comparaveis["valor_estimado"]
    )

    comparaveis["variacao_percentual"] = (
        comparaveis["diferenca"]
        / comparaveis["valor_estimado"]
        * 100
    )

    alertas = comparaveis[
        comparaveis["diferenca"] > 0.01
    ].sort_values(
        "diferenca",
        ascending=False
    )

    campos = [
        "chave", "numero", "ano", "modalidade",
        "situacao", "orgao", "valor_estimado",
        "valor_homologado", "diferenca",
        "variacao_percentual",
    ]

    ocorrencias = []

    campos_monetarios = {
        "valor_estimado",
        "valor_homologado",
        "diferenca",
        "variacao_percentual",
    }

    campos_inteiros = {
        "chave",
        "numero",
        "ano",
    }

    for registro in alertas[campos].head(limite).to_dict("records"):

        ocorrencia = {}

        for chave, valor in registro.items():

            # Primeiro verifica valores ausentes
            if pd.isna(valor):
                ocorrencia[chave] = None

            elif chave in campos_monetarios:
                ocorrencia[chave] = round(float(valor), 2)

            elif chave in campos_inteiros:
                ocorrencia[chave] = int(valor)

            else:
                ocorrencia[chave] = valor

        ocorrencias.append(ocorrencia)

    return {
        "status": "ok",
        "ano": ano,
        "licitacoes_analisadas": len(df),
        "licitacoes_comparaveis": len(comparaveis),
        "licitacoes_com_alertas": len(alertas),
        "ocorrencias": ocorrencias,
        "resultados_limitados": len(alertas) > limite,
        "fonte": "atual_licitacoes.csv",
        "observacao": (
            "Diferenças entre valores estimados e "
            "homologados exigem análise documental. "
            "Não constituem prova de sobrepreço."
        ),
    }

def analisar_impacto_registro(
    ano: int,
    chave: int,
) -> dict:
    """Calcula a participação de uma licitação no total anual."""

    df = carregar_licitacoes()
    df = df[df["ano"] == int(ano)]

    registro = df[df["chave"] == int(chave)]

    if registro.empty:
        return {
            "status": "sem_dados",
            "ano": ano,
            "chave": chave,
        }

    total = df["valor_homologado"].sum(min_count=1)
    valor = registro.iloc[0]["valor_homologado"]

    if pd.isna(valor) or pd.isna(total):
        return {
            "status": "dados_insuficientes",
            "ano": ano,
            "chave": chave,
        }

    total_sem_registro = total - valor

    participacao = (
        valor / total * 100
        if total != 0 else None
    )

    return {
        "status": "ok",
        "ano": ano,
        "chave": chave,
        "valor_registro": round(float(valor), 2),
        "total_original": round(float(total), 2),
        "total_sem_registro": round(
            float(total_sem_registro), 2
        ),
        "participacao_percentual": (
            round(float(participacao), 2)
            if participacao is not None else None
        ),
        "observacao": (
            "A exclusão é apenas uma simulação "
            "de sensibilidade, sem alteração "
            "da base original."
        ),
    }

