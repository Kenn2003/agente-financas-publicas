from src.data.loader import carregar_csvs, PASTA_DADOS, ARQUIVOS

def criar_indice_hash(df, coluna_chave):
    
    indice = {}
    
    for _, linha in df.iterrows():
        
        chave = linha[coluna_chave]
        
        if chave not in indice:
            indice[chave] = []
        
        indice[chave].append(
            linha.to_dict()
        )
    
    return indice

def buscar_indice(indice, chave):
    
    return indice.get(chave, [])

dataframes = carregar_csvs(
    PASTA_DADOS,
    ARQUIVOS
)

df_contratos = dataframes["contratos"]

indice_contratos = criar_indice_hash(
    df_contratos,
    "chave_contrato"
)

print(
    "Quantidade de chaves:",
    len(indice_contratos)
)

indice_contratos = criar_indice_hash(
    df_contratos,
    "chave_contrato"
)

print(
    "Quantidade de chaves:",
    len(indice_contratos)
)

primeira_chave = df_contratos["chave_contrato"].iloc[0]

print("Chave pesquisada:")
print(primeira_chave)

resultado = buscar_indice(
    indice_contratos,
    primeira_chave
)

print("\nResultado:")
print(resultado)


df_pagamentos = dataframes["pagamentos_palmas"]

indice_fornecedores = criar_indice_hash(
    df_pagamentos,
    "cpf_cnpj"
)

print("\nQuantidade de CNPJ/CPF indexados:")
print(len(indice_fornecedores))

primeiro_cnpj = df_pagamentos["cpf_cnpj"].iloc[0]

resultado = buscar_indice(
    indice_fornecedores,
    primeiro_cnpj
)

print("\nCNPJ/CPF pesquisado:")
print(primeiro_cnpj)

print("\nQuantidade de pagamentos encontrados:")
print(len(resultado))


if resultado:
    print("\nPrimeiro pagamento encontrado:")
    print({
        "fornecedor": resultado[0]["fornecedor"],
        "processo": resultado[0]["processo"],
        "empenho": resultado[0]["empenho"],
        "valor_pago": resultado[0]["valor_pago"]
    })