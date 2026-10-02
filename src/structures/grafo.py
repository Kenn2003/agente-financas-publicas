import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import textwrap

from src.data.loader import carregar_csvs, PASTA_DADOS, ARQUIVOS

dataframes = carregar_csvs(
    PASTA_DADOS,
    ARQUIVOS
)

def criar_grafo_hierarquico(
    df,
    colunas,
    tipos,
    limite=20
):
    
    df_grafo = (
        df[colunas]
        .dropna()
        .drop_duplicates()
        .head(limite)
        .copy()
    )

    G = nx.Graph()

    for _, linha in df_grafo.iterrows():
    
        for i in range(len(colunas) - 1):
    
            atual = linha[colunas[i]]
            proximo = linha[colunas[i + 1]]
            
            atual_id = "::".join(
                str(linha[colunas[j]])
                for j in range(i + 1)
            )
            
            proximo_id = "::".join(
                str(linha[colunas[j]])
                for j in range(i + 2)
            )
    
            G.add_node(
                atual_id,
                tipo=tipos[i],
                label=str(atual)
            )
            
            G.add_node(
                proximo_id,
                tipo=tipos[i + 1],
                label=str(proximo)
            )
            
            G.add_edge(
                atual_id,
                proximo_id
            )

    return G, df_grafo

def plotar_grafo_hierarquico(G, tipos):

    plt.figure(figsize=(16, 9))

    pos = {}

    # 1. Separar os nós por tipo
    nos_por_tipo = {}
    
    for tipo in tipos:
    
        nos_por_tipo[tipo] = [
            no for no, dados in G.nodes(data=True)
            if dados.get("tipo") == tipo
        ]

    # 2. Calcular a posição de cada nível
    for indice_nivel, tipo in enumerate(tipos):
    
        y = len(tipos) - 1 - indice_nivel
    
        for i, no in enumerate(nos_por_tipo[tipo]):
    
            pos[no] = (i, y)
        
    # 3. Desenhar as arestas
    nx.draw_networkx_edges(
        G,
        pos,
        width=1.2,
        alpha=0.5,
        edge_color="gray"
    )


    cores = plt.cm.Blues(
        np.linspace(0.4, 0.9, len(tipos))
    )
    
    # 4. Desenhar os nós de cada nível
    for indice_nivel, tipo in enumerate(tipos):
        nx.draw_networkx_nodes(
            G,
            pos,
            nodelist= nos_por_tipo[tipo],
            node_color=[cores[indice_nivel]],
            node_size=1500,
            label=str(tipo)
        )

    # 5. Recuperar os labels armazenados no grafo

        labels_nos = {
            no: "\n".join(
              textwrap.wrap(
                  str(G.nodes[no].get("label", no)),
                 width=20
              )
         )
          for no in nos_por_tipo[tipo]
    }
            
    # 6. Desenhar os labels
        nx.draw_networkx_labels(
              G,
              pos,
              font_size=8,
              font_weight="bold",
              labels=labels_nos
           )

    # 7. Finalizar o gráfico

    plt.title(
        "Grafo Hierárquico",
        fontsize=15,
        fontweight="bold"
    )

    plt.legend(
        loc="upper right",
        frameon=True
    )

    plt.axis("off")
    plt.tight_layout()
    plt.show()
    
    
colunas = [
    "Nome",
    "Valor Total da Dívida",
    "Data da Inscrição"
]

tipos = [
    "orgao",
    "Valor Total da Dívida",
    "Data da Inscrição"
]

G, df_grafo = criar_grafo_hierarquico(
    dataframes["relatorio_dívida_ativa"],
    colunas,
    tipos,
    limite = 10
)

plotar_grafo_hierarquico(G, tipos)

colunas = ["orgao", "licitacao", "chave_contrato", "contratados"]
tipos = ["orgao", "licitacao", "contrato", "contratado"]

G, df_grafo = criar_grafo_hierarquico(
    dataframes["contratos"],
    colunas,
    tipos,
    limite=10
)

plotar_grafo_hierarquico(G, tipos)