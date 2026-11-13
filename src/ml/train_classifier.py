import pandas as pd
from sklearn.ensemble import RandomForestClassifier
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


COLUNAS = [
    "valor_divida",
    "log_valor_divida",
    "ano_inscricao",
    "mes_inscricao",
    "trimestre_inscricao",
    "dia_semana_inscricao"
]


def avaliar_modelo(modelo, X, y, nome):
    previsoes = modelo.predict(X)

    print(f"\n===== {nome} =====")
    print("Acurácia:", accuracy_score(y, previsoes))
    print("Precisão:", precision_score(y, previsoes, zero_division=0))
    print("Recall:", recall_score(y, previsoes, zero_division=0))
    print("F1-score:", f1_score(y, previsoes, zero_division=0))
    print("Matriz de confusão:")
    print(confusion_matrix(y, previsoes))


def main():
    # 1. Carregamento e preparação dos dados
    dados = carregar_base_divida()
    features = construir_features(dados)
    base = adicionar_alvos_sinteticos(features)

    # 2. Separação temporal dos três conjuntos

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

    X_treino = treino[COLUNAS]
    y_treino = treino["inadimplente_sintetico"]

    X_validacao = validacao[COLUNAS]
    y_validacao = validacao["inadimplente_sintetico"]

    X_teste = teste[COLUNAS]
    y_teste = teste["inadimplente_sintetico"]

    print("Registros de treinamento:", len(treino))
    print("Registros de validação:", len(validacao))
    print("Registros de teste:", len(teste))

    # 4. Teste de diferentes configurações
    configuracoes = [
        {"n_estimators": 100, "max_depth": 5, "min_samples_leaf": 5},
        {"n_estimators": 100, "max_depth": 10, "min_samples_leaf": 5},
        {"n_estimators": 200, "max_depth": 10, "min_samples_leaf": 10},
        {"n_estimators": 200, "max_depth": 15, "min_samples_leaf": 5},
        {"n_estimators": 200, "max_depth": None, "min_samples_leaf": 10}
    ]

    melhor_f1 = -1
    melhores_parametros = None

    for parametros in configuracoes:
        modelo = RandomForestClassifier(
            **parametros,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )

        modelo.fit(X_treino, y_treino)

        previsoes = modelo.predict(X_validacao)
        resultado_f1 = f1_score(
            y_validacao,
            previsoes,
            zero_division=0
        )

        print("\nConfiguração:", parametros)
        print("F1-score de validação:", resultado_f1)

        if resultado_f1 > melhor_f1:
            melhor_f1 = resultado_f1
            melhores_parametros = parametros

    # 5. Treinamento final com treino + validação

    X_treino_final = pd.concat([X_treino, X_validacao])
    y_treino_final = pd.concat([y_treino, y_validacao])

    modelo_final = RandomForestClassifier(
        **melhores_parametros,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    modelo_final.fit(X_treino_final, y_treino_final)

    print("\n===== MELHORES PARÂMETROS =====")
    print(melhores_parametros)
    print("Melhor F1-score na validação:", melhor_f1)

    # 6. Avaliação final no teste, que não participou da seleção
    avaliar_modelo(
        modelo_final,
        X_teste,
        y_teste,
        "Random Forest - Teste Final"
    )


if __name__ == "__main__":
    main()
