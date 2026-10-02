import heapq

from src.data.loader import carregar_csvs, PASTA_DADOS, ARQUIVOS
from src.data.processing import converter_moeda_brasileira

def criar_heap_prioridade(
    df,
    coluna_prioridade,
    coluna_identificador,
    coluna_data=None
):
    
    heap = []
    
    for _, linha in df.iterrows():
        prioridade = linha[coluna_prioridade]
        identificador = linha[coluna_identificador]
        
        data = (
           linha[coluna_data]
           if coluna_data
           else None
       )

        heapq.heappush(
           heap,
           (-prioridade, identificador, data)
       )
    
    return heap


def criar_heap_prioridade(
    df,
    coluna_prioridade,
    coluna_identificador,
    coluna_data=None
):
    
    heap = []

    for _, linha in df.iterrows():
        
        prioridade = converter_moeda_brasileira(
            linha[coluna_prioridade]
        )
        
        identificador = linha[coluna_identificador]
        
        data = (
            linha[coluna_data]
            if coluna_data
            else None
        )
        
        if prioridade is not None:
            heapq.heappush(
                heap,
                (-prioridade, identificador, data)
            )
    
    return heap

def remover_maior_prioridade(heap):
    
    if not heap:
        return None
    
    prioridade, identificador, data = heapq.heappop(heap)
    
    return {
        "prioridade": -prioridade,
        "identificador": identificador,
        "data": data
    }

dataframes = carregar_csvs(
    PASTA_DADOS,
    ARQUIVOS
)

df_divida = dataframes["divida_ativa"]

heap_dividas = criar_heap_prioridade(
    df_divida,
    coluna_prioridade="Valor Total da Dívida",
    coluna_identificador="Nome",
    coluna_data="Data da Inscrição"
)

print("\nQuantidade no heap:")
print(len(heap_dividas))

print("\n5 maiores prioridades:")

for _ in range(5):
    print(remover_maior_prioridade(heap_dividas))