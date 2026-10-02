from src.data.loader import (
    carregar_csvs,
    PASTA_DADOS,
    ARQUIVOS
)

from src.structures.grafo import (
    criar_grafo_hierarquico,
    plotar_grafo_hierarquico
)


if __name__ == "__main__":

    # =========================================================
    # CARREGAMENTO DOS DADOS
    # =========================================================

    dataframes = carregar_csvs(
        PASTA_DADOS,
        ARQUIVOS
    )


    # =========================================================
    # TESTE 1 - LICITAÇÕES
    # Órgão → Modalidade → Processo
    # =========================================================

    print("\n=== TESTE GRAFO: LICITAÇÕES ===")

    G_licitacoes, df_licitacoes = criar_grafo_hierarquico(
        dataframes["licitacoes"],
        colunas=[
            "orgao",
            "modalidade",
            "numero_processo"
        ],
        tipos=[
            "orgao",
            "modalidade",
            "processo"
        ],
        limite=10
    )

    print("Registros utilizados:", len(df_licitacoes))
    print("Quantidade de nós:", G_licitacoes.number_of_nodes())
    print("Quantidade de arestas:", G_licitacoes.number_of_edges())

    plotar_grafo_hierarquico(
        G_licitacoes,
        [
            "orgao",
            "modalidade",
            "processo"
        ]
    )


    # =========================================================
    # TESTE 2 - CONTRATOS
    # Órgão → Licitação → Contrato → Contratado
    # =========================================================

    print("\n=== TESTE GRAFO: CONTRATOS ===")

    G_contratos, df_contratos = criar_grafo_hierarquico(
        dataframes["contratos"],
        colunas=[
            "orgao",
            "licitacao",
            "chave_contrato",
            "contratados"
        ],
        tipos=[
            "orgao",
            "licitacao",
            "contrato",
            "contratado"
        ],
        limite=10
    )

    print("Registros utilizados:", len(df_contratos))
    print("Quantidade de nós:", G_contratos.number_of_nodes())
    print("Quantidade de arestas:", G_contratos.number_of_edges())

    plotar_grafo_hierarquico(
        G_contratos,
        [
            "orgao",
            "licitacao",
            "contrato",
            "contratado"
        ]
    )


    # =========================================================
    # TESTE 3 - PAGAMENTOS
    # Unidade → Fornecedor → Processo → Empenho
    # =========================================================

    print("\n=== TESTE GRAFO: PAGAMENTOS ===")

    G_pagamentos, df_pagamentos = criar_grafo_hierarquico(
        dataframes["pagamentos_palmas"],
        colunas=[
            "unidade",
            "fornecedor",
            "processo",
            "empenho"
        ],
        tipos=[
            "unidade",
            "fornecedor",
            "processo",
            "empenho"
        ],
        limite=10
    )

    print("Registros utilizados:", len(df_pagamentos))
    print("Quantidade de nós:", G_pagamentos.number_of_nodes())
    print("Quantidade de arestas:", G_pagamentos.number_of_edges())

    plotar_grafo_hierarquico(
        G_pagamentos,
        [
            "unidade",
            "fornecedor",
            "processo",
            "empenho"
        ]
    )