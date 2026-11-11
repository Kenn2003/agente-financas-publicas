
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

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

COLUNA_ALVO = "taxa_recuperacao_sintetica"


def classificar_potencial(taxa):
    if taxa >= 0.70:
        return "Alto"
    elif taxa >= 0.40:
        return "Médio"
    else:
        return "Baixo"


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


def main():
    print("Carregando dados...")

    base = carregar_base_divida()
    base = construir_features(base)
    base = adicionar_alvos_sinteticos(base)

    treino, validacao, teste = dividir_dados(base)

    print("\n===== DIVISÃO DOS DADOS =====")
    print("Treinamento:", len(treino))
    print("Validação:", len(validacao))
    print("Teste:", len(teste))

    X_treino = treino[COLUNAS_FEATURES]
    y_treino = treino[COLUNA_ALVO]

    X_validacao = validacao[COLUNAS_FEATURES]
    y_validacao = validacao[COLUNA_ALVO]

    configuracoes = [
        {"n_estimators": 100, "max_depth": 5, "min_samples_leaf": 5},
        {"n_estimators": 100, "max_depth": 10, "min_samples_leaf": 5},
        {"n_estimators": 200, "max_depth": 10, "min_samples_leaf": 10},
        {"n_estimators": 200, "max_depth": 15, "min_samples_leaf": 5},
        {"n_estimators": 200, "max_depth": None, "min_samples_leaf": 10}
    ]

    melhor_modelo = None
    melhor_mae = float("inf")
    melhores_parametros = None

    print("\n===== TESTE DE CONFIGURAÇÕES =====")

    for parametros in configuracoes:
        modelo = RandomForestRegressor(
            **parametros,
            random_state=42,
            n_jobs=-1
        )

        modelo.fit(X_treino, y_treino)

        previsoes = modelo.predict(X_validacao)
        previsoes = np.clip(previsoes, 0, 1)

        mae = mean_absolute_error(y_validacao, previsoes)

        print("\nConfiguração:", parametros)
        print("MAE de validação:", round(mae, 4))

        if mae < melhor_mae:
            melhor_mae = mae
            melhor_modelo = modelo
            melhores_parametros = parametros

    print("\n===== MELHORES PARÂMETROS =====")
    print(melhores_parametros)
    print("Melhor MAE na validação:", round(melhor_mae, 4))

    # Treina novamente com treinamento + validação
    dados_treino_final = pd.concat([treino, validacao])

    X_treino_final = dados_treino_final[COLUNAS_FEATURES]
    y_treino_final = dados_treino_final[COLUNA_ALVO]

    modelo_final = RandomForestRegressor(
        **melhores_parametros,
        random_state=42,
        n_jobs=-1
    )

    modelo_final.fit(X_treino_final, y_treino_final)

    # Avaliação final no conjunto de teste
    X_teste = teste[COLUNAS_FEATURES]
    y_teste = teste[COLUNA_ALVO]

    previsoes_teste = modelo_final.predict(X_teste)
    previsoes_teste = np.clip(previsoes_teste, 0, 1)

    mae = mean_absolute_error(y_teste, previsoes_teste)
    rmse = np.sqrt(mean_squared_error(y_teste, previsoes_teste))
    r2 = r2_score(y_teste, previsoes_teste)

    print("\n===== MODELO DE RECUPERAÇÃO - TESTE FINAL =====")
    print("MAE:", round(mae, 4))
    print("RMSE:", round(rmse, 4))
    print("R²:", round(r2, 4))

    resultado = teste[["valor_divida"]].copy()
    resultado["taxa_recuperacao_prevista"] = previsoes_teste
    resultado["potencial_recuperacao"] = (
        resultado["taxa_recuperacao_prevista"]
        .apply(classificar_potencial)
    )

    print("\n===== DISTRIBUIÇÃO DO POTENCIAL =====")
    print(resultado["potencial_recuperacao"].value_counts())

    print("\n===== EXEMPLOS DE PREVISÕES =====")
    print(resultado.head(10).to_string(index=False))

    print("\nObservação: os alvos utilizados são sintéticos.")
    print("Os resultados demonstram o funcionamento do pipeline,")
    print("não uma previsão real de recuperação de dívidas.")


if __name__ == "__main__":
    main()
