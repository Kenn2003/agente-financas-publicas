import heapq

from src.data.loader import carregar_csvs, PASTA_DADOS, ARQUIVOS
from src.data.processing import converter_moeda_brasileira

dataframes = carregar_csvs(
    PASTA_DADOS,
    ARQUIVOS
)

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


df_divida = dataframes["divida_ativa"]

print(df_divida["Valor Total da Dívida"].dtype)
print(df_divida["Valor Total da Dívida"].head(10))