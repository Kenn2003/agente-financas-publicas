
import pandas as pd


def split_temporal(
    df,
    coluna_data="data_inscricao",
    proporcao_treino=0.8
):
    """
    Divide os dados cronologicamente em treino e teste.

    Os registros mais antigos ficam no treino.
    Os registros mais recentes ficam no teste.

    Datas iguais não são separadas entre os conjuntos.
    """

    if coluna_data not in df.columns:
        raise ValueError(
            f"Coluna '{coluna_data}' não encontrada."
        )

    if not 0 < proporcao_treino < 1:
        raise ValueError(
            "A proporção de treino deve estar entre 0 e 1."
        )

    base = df.copy()

    base[coluna_data] = pd.to_datetime(
        base[coluna_data],
        errors="coerce"
    )

    base = base.dropna(subset=[coluna_data])

    datas = sorted(base[coluna_data].unique())

    if len(datas) < 2:
        raise ValueError(
            "São necessárias pelo menos duas datas diferentes."
        )

    indice_corte = int(len(datas) * proporcao_treino)

    indice_corte = max(
        1,
        min(indice_corte, len(datas) - 1)
    )

    data_corte = datas[indice_corte]

    treino = base[
        base[coluna_data] < data_corte
    ].copy()

    teste = base[
        base[coluna_data] >= data_corte
    ].copy()

    return treino, teste


if __name__ == "__main__":

    from features import (
        carregar_base_divida,
        construir_features
    )

    dados = carregar_base_divida()
    features = construir_features(dados)

    treino, teste = split_temporal(features)

    print("DIVISÃO TEMPORAL")
    print("-" * 40)

    print("Total de registros:", len(features))
    print("Treino:", len(treino))
    print("Teste:", len(teste))

    print("\nPeríodo de treino:")
    print(
        treino["data_inscricao"].min(),
        "até",
        treino["data_inscricao"].max()
    )

    print("\nPeríodo de teste:")
    print(
        teste["data_inscricao"].min(),
        "até",
        teste["data_inscricao"].max()
    )
