
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from features import (
    carregar_base_divida,
    construir_features,
    adicionar_alvos_sinteticos
)


COLUNAS_FEATURES = [
    "valor_divida",
    "log_valor_divida",
    "ano_inscricao",
    "mes_inscricao",
    "trimestre_inscricao",
    "dia_semana_inscricao"
]


def dividir_dados(base):
    treino = base[
        base["data_inscricao"] <= pd.Timestamp("2026-02-05")
    ].copy()

    validacao = base[
        (base["data_inscricao"] >= pd.Timestamp("2026-03-12")) &
        (base["data_inscricao"] <= pd.Timestamp("2026-06-04"))
    ].copy()

    teste = base[
        base["data_inscricao"] >= pd.Timestamp("2026-06-23")
    ].copy()

    return treino, validacao, teste


def avaliar_classificador(treino_final, teste):
    print("\n===== AVALIAÇÃO DO CLASSIFICADOR =====")

    modelo = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    X_treino = treino_final[COLUNAS_FEATURES]
    y_treino = treino_final["inadimplente_sintetico"]

    X_teste = teste[COLUNAS_FEATURES]
    y_teste = teste["inadimplente_sintetico"]

    modelo.fit(X_treino, y_treino)

    previsoes = modelo.predict(X_teste)

    print("Acurácia:", round(accuracy_score(y_teste, previsoes), 4))
    print("Precisão:", round(precision_score(
        y_teste, previsoes, zero_division=0
    ), 4))
    print("Recall:", round(recall_score(
        y_teste, previsoes, zero_division=0
    ), 4))
    print("F1-score:", round(f1_score(
        y_teste, previsoes, zero_division=0
    ), 4))

    print("\nMatriz de confusão:")
    print(confusion_matrix(y_teste, previsoes))

    print("\nImportância das variáveis:")
    for nome, importancia in sorted(
        zip(COLUNAS_FEATURES, modelo.feature_importances_),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"{nome}: {importancia:.4f}")


def avaliar_recuperacao(treino_final, teste):
    print("\n===== AVALIAÇÃO DO MODELO DE RECUPERAÇÃO =====")

    modelo = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )

    X_treino = treino_final[COLUNAS_FEATURES]
    y_treino = treino_final["taxa_recuperacao_sintetica"]

    X_teste = teste[COLUNAS_FEATURES]
    y_teste = teste["taxa_recuperacao_sintetica"]

    modelo.fit(X_treino, y_treino)

    previsoes = modelo.predict(X_teste)
    previsoes = np.clip(previsoes, 0, 1)

    mae = mean_absolute_error(y_teste, previsoes)
    rmse = np.sqrt(mean_squared_error(y_teste, previsoes))
    r2 = r2_score(y_teste, previsoes)

    print("MAE:", round(mae, 4))
    print("RMSE:", round(rmse, 4))
    print("R²:", round(r2, 4))

    print("\nImportância das variáveis:")
    for nome, importancia in sorted(
        zip(COLUNAS_FEATURES, modelo.feature_importances_),
        key=lambda item: item[1],
        reverse=True
    ):
        print(f"{nome}: {importancia:.4f}")


def main():
    print("Carregando dados para avaliação...")

    base = carregar_base_divida()
    base = construir_features(base)
    base = adicionar_alvos_sinteticos(base)

    treino, validacao, teste = dividir_dados(base)

    treino_final = pd.concat(
        [treino, validacao],
        ignore_index=True
    )

    print("\n===== DIVISÃO DOS DADOS =====")
    print("Treinamento + validação:", len(treino_final))
    print("Teste:", len(teste))

    avaliar_classificador(treino_final, teste)
    avaliar_recuperacao(treino_final, teste)

    print("\n===== OBSERVAÇÃO =====")
    print("Os alvos utilizados são sintéticos.")
    print("As métricas demonstram o funcionamento do pipeline.")
    print("Não representam previsões reais de inadimplência")
    print("ou de recuperação de dívidas.")


if __name__ == "__main__":
    main()
