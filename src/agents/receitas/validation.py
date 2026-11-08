import pandas as pd

from tools import ARQUIVO, CODIGOS_TOTAL


def validar_base_receitas(ano=2024):
    colunas = [
        "ano", "mes", "orgao", "codigo",
        "descricao", "valor_arrecado_mes",
        "valor_arrecado_periodo"
    ]

    df = pd.read_csv(
        ARQUIVO,
        usecols=colunas,
        dtype={"codigo": "string"},
        low_memory=False
    )

    df = df[df["ano"] == ano].copy()

    # 1. Duplicidades por chave lógica
    chave = ["ano", "mes", "orgao", "codigo"]

    duplicados = df[
        df.duplicated(subset=chave, keep=False)
    ]

    print("\n1. DUPLICIDADES POR CHAVE")
    print("Registros envolvidos:", len(duplicados))
    print(duplicados[chave].head(10).to_string(index=False))

    # 2. Códigos superiores disponíveis
    print("\n2. CATEGORIAS DE PRIMEIRO NÍVEL")

    superiores = df[
        df["codigo"].str.match(
            r"^[0-9]\.0\.0\.0\.00\.0\.0$",
            na=False
        )
    ]

    resumo = (
        superiores.groupby(["codigo", "descricao"])
        ["valor_arrecado_mes"]
        .agg(["count", "sum"])
        .reset_index()
    )

    print(resumo.to_string(index=False))

    codigos_encontrados = set(superiores["codigo"])
    print(
        "\nCódigos ausentes da configuração:",
        codigos_encontrados - CODIGOS_TOTAL
    )

    # 3. Consistência entre mensal e acumulado
    print("\n3. CONSISTÊNCIA DO ACUMULADO")

    selecionados = superiores[
        superiores["codigo"].isin(CODIGOS_TOTAL)
    ].copy()

    selecionados = selecionados.sort_values(
        ["orgao", "codigo", "mes"]
    )

    selecionados["soma_acumulada"] = (
        selecionados.groupby(["orgao", "codigo"])
        ["valor_arrecado_mes"].cumsum()
    )

    selecionados["diferenca"] = (
        selecionados["valor_arrecado_periodo"]
        - selecionados["soma_acumulada"]
    )

    divergencias = selecionados[
        selecionados["diferenca"].abs() > 0.05
    ]

    print("Registros divergentes:", len(divergencias))

    print(
        divergencias[
            ["orgao", "codigo", "mes", "diferenca"]
        ].head(15).to_string(index=False)
    )


if __name__ == "__main__":
    validar_base_receitas(2024)
