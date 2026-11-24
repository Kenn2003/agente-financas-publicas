
"""Avaliacao experimental dos modelos da Sprint 04.

Os alvos sao sinteticos e os grupos representam caracteristicas
das dividas, nao atributos demograficos dos contribuintes.
"""

import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import confusion_matrix

from src.governance.fairness import avaliar_fairness


ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = ROOT / "relatorio_dívida_ativa.csv"
MODELS_DIR = ROOT / "models"
OUTPUT = ROOT / "docs/evidencias/fairness"

FEATURES = ["log_valor_divida", "idade_divida_dias"]

SEED = 42
DATA_REFERENCIA = pd.Timestamp("2026-10-01")
FIM_VALIDACAO = pd.Timestamp("2026-06-30")


def preparar_dados():
    """Reproduz a preparacao do notebook da Sprint 04."""

    raw = pd.read_csv(
        DATA_PATH,
        sep=";",
        encoding="utf-8-sig",
    ).drop_duplicates()

    df = raw[
        ["Valor Total da Dívida", "Data da Inscrição"]
    ].copy()

    df["valor_divida"] = pd.to_numeric(
        df["Valor Total da Dívida"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )

    df["data_inscricao"] = pd.to_datetime(
        df["Data da Inscrição"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    df = (
        df.dropna(subset=["valor_divida", "data_inscricao"])
        .loc[lambda x: x["valor_divida"] >= 0]
        .sort_values("data_inscricao")
        .reset_index(drop=True)
    )

    df["idade_divida_dias"] = (
        DATA_REFERENCIA - df["data_inscricao"]
    ).dt.days.clip(lower=0)

    df["log_valor_divida"] = np.log1p(
        df["valor_divida"]
    )

    logit = (
        -3.8
        + 0.35 * df["log_valor_divida"]
        + 0.35 * (df["idade_divida_dias"] / 365)
    )

    probabilidade = 1 / (1 + np.exp(-logit))

    df["inadimplencia_proxy"] = (
        np.random.default_rng(SEED).random(len(df))
        < probabilidade
    ).astype(int)

    score = (
        0.65 * np.exp(
            -(df["idade_divida_dias"] / 365) / 3
        )
        + 0.35 * np.exp(
            -df["log_valor_divida"] / 5
        )
    ).clip(0, 1)

    df["recuperabilidade_proxy"] = pd.cut(
        score,
        bins=[-np.inf, 0.65, 0.75, np.inf],
        labels=["baixa", "media", "alta"],
        right=False,
    ).astype(str)

    return df


def criar_grupos(df):
    """Cria subgrupos exclusivamente financeiros e temporais."""

    return {
        "faixa_valor": pd.cut(
            df["valor_divida"],
            [-np.inf, 500, 5000, np.inf],
            labels=[
                "ate_500",
                "500_a_5000",
                "acima_5000",
            ],
        ).astype(str),

        "faixa_idade": pd.cut(
            df["idade_divida_dias"],
            [-np.inf, 30, 60, np.inf],
            labels=[
                "ate_30_dias",
                "31_a_60_dias",
                "acima_60_dias",
            ],
        ).astype(str),
    }


def avaliar_subgrupos(y_true, y_pred, grupos):
    return {
        nome: avaliar_fairness(y_true, y_pred, valores)
        for nome, valores in grupos.items()
    }


def carregar_artefato(nome):
    artefato = joblib.load(MODELS_DIR / nome)

    if artefato["features"] != FEATURES:
        raise ValueError("Features incompativeis.")

    if artefato["target_status"] != "sintetico_proxy_nao_observado":
        raise ValueError("Origem do alvo nao confirmada.")

    return artefato


def executar():
    df = preparar_dados()

    # Utiliza somente a particao de teste original.
    teste = df.loc[
        df["data_inscricao"] > FIM_VALIDACAO
    ].copy()

    if teste.empty:
        raise ValueError("Particao de teste vazia.")

    X = teste[FEATURES].astype(float)
    grupos = criar_grupos(teste)

    baseline = carregar_artefato("baseline.joblib")
    inadimplencia = carregar_artefato("inadimplencia.joblib")
    recuperabilidade = carregar_artefato("recuperabilidade.joblib")

    y = teste["inadimplencia_proxy"]
    y_rec = teste["recuperabilidade_proxy"]

    pred = inadimplencia["estimator"].predict(X)
    pred_rec = recuperabilidade["estimator"].predict(X)

    # Verifica a reproducao das matrizes da Sprint 04.
    matriz = confusion_matrix(y, pred, labels=[0, 1]).tolist()

    esperada = inadimplencia[
        "test_metrics_proxy"
    ]["matriz_confusao_0_1"]

    if matriz != esperada:
        raise ValueError(
            "Matriz de inadimplencia diferente da Sprint 04."
        )

    classes = ["baixa", "media", "alta"]

    matriz_rec = confusion_matrix(
        y_rec, pred_rec, labels=classes
    ).tolist()

    esperada_rec = recuperabilidade[
        "test_metrics_proxy"
    ]["matriz_confusao_baixa_media_alta"]

    if matriz_rec != esperada_rec:
        raise ValueError(
            "Matriz de recuperabilidade diferente da Sprint 04."
        )

    relatorio = {
        "natureza": "diagnostico_experimental",
        "alvos": "sinteticos_nao_observados",
        "unidade_analise": "registros_de_divida",
        "registros_validos": len(df),
        "registros_teste": len(teste),
        "seed": SEED,
        "matrizes_originais_reproduzidas": True,
        "versoes": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "grupos_observados": {
            nome: sorted(set(valores))
            for nome, valores in grupos.items()
        },
        "modelos": {},
    }

    for nome, modelo in baseline["estimators"].items():
        relatorio["modelos"][nome] = avaliar_subgrupos(
            y,
            modelo.predict(X),
            grupos,
        )

    relatorio["modelos"]["random_forest_inadimplencia"] = (
        avaliar_subgrupos(y, pred, grupos)
    )

    # Avaliacao multiclasse: uma classe contra as demais.
    for classe in classes:
        relatorio["modelos"][
            f"recuperabilidade_{classe}"
        ] = avaliar_subgrupos(
            (y_rec == classe).astype(int),
            (pred_rec == classe).astype(int),
            grupos,
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)

    caminho = OUTPUT / "metricas_modelos_proxy.json"

    caminho.write_text(
        json.dumps(
            relatorio,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    print(json.dumps(
        relatorio,
        indent=2,
        ensure_ascii=False,
    ))

    print(f"\nRelatorio salvo em: {caminho}")


if __name__ == "__main__":
    executar()
