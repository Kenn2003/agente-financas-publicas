
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from features import (
    carregar_base_divida,
    construir_features,
    adicionar_alvos_sinteticos
)

from split_temporal import split_temporal


def avaliar_modelo(nome, modelo, X_teste, y_teste):
    previsoes = modelo.predict(X_teste)

    print(f"\n===== {nome} =====")
    print("Acurácia:", accuracy_score(y_teste, previsoes))
    print("Precisão:", precision_score(y_teste, previsoes, zero_division=0))
    print("Recall:", recall_score(y_teste, previsoes, zero_division=0))
    print("F1-score:", f1_score(y_teste, previsoes, zero_division=0))
    print("Matriz de confusão:")
    print(confusion_matrix(y_teste, previsoes))


def main():
    dados = carregar_base_divida()
    features = construir_features(dados)
    dados_sinteticos = adicionar_alvos_sinteticos(features)

    treino, teste = split_temporal(dados_sinteticos)

    colunas = [
        "valor_divida",
        "log_valor_divida",
        "ano_inscricao",
        "mes_inscricao",
        "trimestre_inscricao",
        "dia_semana_inscricao"
    ]

    X_treino = treino[colunas]
    X_teste = teste[colunas]

    y_treino = treino["inadimplente_sintetico"]
    y_teste = teste["inadimplente_sintetico"]

    # Modelo 1: Regressão Logística
    regressao = Pipeline([
        ("escala", StandardScaler()),
        ("modelo", LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ))
    ])

    regressao.fit(X_treino, y_treino)

    avaliar_modelo(
        "Regressão Logística",
        regressao,
        X_teste,
        y_teste
    )

    # Modelo 2: Árvore de Decisão
    arvore = DecisionTreeClassifier(
        max_depth=5,
        class_weight="balanced",
        random_state=42
    )

    arvore.fit(X_treino, y_treino)

    avaliar_modelo(
        "Árvore de Decisão",
        arvore,
        X_teste,
        y_teste
    )


if __name__ == "__main__":
    main()
