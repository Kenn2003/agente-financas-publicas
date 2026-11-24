
"""Metricas experimentais de equidade algoritmica — Sprint 05.

Nao utilizar os resultados como autorizacao de cobranca
ou comprovacao de equidade demografica real.
"""

import pandas as pd


def divisao_segura(numerador, denominador):
    return numerador / denominador if denominador else None


def calcular_metricas_grupo(y_true, y_pred):
    """Calcula metricas binarias para um subgrupo."""

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    n = len(y_true)

    return {
        "n": n,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "taxa_selecao": divisao_segura(tp + fp, n),
        "tpr": divisao_segura(tp, tp + fn),
        "fpr": divisao_segura(fp, fp + tn),
        "fnr": divisao_segura(fn, fn + tp),
        "precisao": divisao_segura(tp, tp + fp),
        "acuracia": divisao_segura(tp + tn, n),
    }


def diferenca_metricas(resultados, metrica):
    """Calcula a diferenca entre o maior e o menor valor."""

    valores = [grupo[metrica] for grupo in resultados]

    if len(valores) < 2 or any(v is None for v in valores):
        return None

    return max(valores) - min(valores)


def avaliar_fairness(y_true, y_pred, grupos):
    """Avalia disparidades entre grupos em classificacao binaria."""

    y_true = list(y_true)
    y_pred = list(y_pred)
    grupos = list(grupos)

    if not (len(y_true) == len(y_pred) == len(grupos)):
        raise ValueError("As entradas devem possuir o mesmo tamanho.")

    if not y_true:
        raise ValueError("A amostra nao pode ser vazia.")

    df = pd.DataFrame({
        "real_proxy": y_true,
        "predito": y_pred,
        "grupo": grupos,
    })

    if not df["real_proxy"].isin([0, 1]).all():
        raise ValueError("Os rotulos devem ser binarios.")

    if not df["predito"].isin([0, 1]).all():
        raise ValueError("As previsoes devem ser binarias.")

    if not df["grupo"].map(
        lambda x: isinstance(x, str) and bool(x.strip())
    ).all():
        raise ValueError("Os grupos devem possuir nomes validos.")

    resultados = []

    for grupo, bloco in df.groupby("grupo", observed=True):
        metricas = calcular_metricas_grupo(
            bloco["real_proxy"],
            bloco["predito"],
        )

        resultados.append({
            "grupo": grupo,
            **metricas,
        })

    taxas = [g["taxa_selecao"] for g in resultados]

    disparate_impact = None

    if len(taxas) >= 2:
        disparate_impact = divisao_segura(min(taxas), max(taxas))

    return {
        "grupos": resultados,
        "demographic_parity_difference": diferenca_metricas(
            resultados, "taxa_selecao"
        ),
        "equal_opportunity_difference": diferenca_metricas(
            resultados, "tpr"
        ),
        "disparate_impact_ratio": disparate_impact,
        "false_positive_rate_difference": diferenca_metricas(
            resultados, "fpr"
        ),
        "false_negative_rate_difference": diferenca_metricas(
            resultados, "fnr"
        ),
        "finalidade": "diagnostico_experimental",
    }
