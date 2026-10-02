# Arquitetura de Dados --- Sprint 2

## 1. Visão geral

O projeto **Agente Inteligente para Análise da Gestão Financeira
Municipal** utiliza dados públicos do Município de Palmas-TO para
estruturar análises sobre receitas, despesas, licitações, contratos,
pagamentos, servidores, folha de pagamento, dívida ativa e sanções
administrativas.

Nesta Sprint, a arquitetura foi organizada para separar a **origem dos
dados**, o **carregamento**, o **pré-processamento**, as **estruturas de
dados**, a **persistência relacional** e as futuras camadas analíticas.

``` text
Fontes públicas / CSV
        |
        v
loader.py / preprocessing.py
        |
        v
DataFrames Pandas
        |
        +--------+--------+
        |        |        |
      Grafos    Heap     Hash
     NetworkX  heapq     dict
        |        |        |
        +--------+--------+
                 |
                 v
       Banco relacional
      PostgreSQL / Supabase
                 |
                 v
         Camada analítica
                 |
                 v
            Agente de IA
```

## 2. Fontes de dados

Na Sprint 2, os arquivos CSV constituem a camada de dados brutos. As
principais bases são:

  -----------------------------------------------------------------------------
  Base                                      Conteúdo principal
  ----------------------------------------- -----------------------------------
  `contratos.csv`                           Contratos administrativos

  `despesas.csv`                            Empenhos, fornecedores, liquidações
                                            e pagamentos

  `receita_acessoinformacao.csv`            Receitas por órgão e classificação

  `receita_palmas.csv`                      Receitas consolidadas

  `servidores.csv`                          Informações funcionais dos
                                            servidores

  `licitacoes.csv`                          Processos e modalidades de
                                            licitação

  `folha_palmas.csv`                        Folha de pagamento

  `pagamentos_palmas.csv`                   Pagamentos, fornecedores, processos
                                            e empenhos

  `relatorio_dívida_ativa.csv`              Nome, valor da dívida e data de
                                            inscrição

  `relatorio_licitacoes.csv`                Relatório complementar de
                                            licitações

  `relatorio_sanções_administrativas.csv`   Sanções administrativas
  -----------------------------------------------------------------------------

Os arquivos originais são preservados para garantir rastreabilidade
entre a fonte pública e os dados utilizados pelo sistema.

## 3. Camada de carregamento

O módulo `src/data/loader.py` centraliza o carregamento dos arquivos. A
função `carregar_csvs()` recebe o diretório e o dicionário de arquivos e
retorna um dicionário de DataFrames.

``` python
dataframes = {
    "contratos": df_contratos,
    "despesas": df_despesas,
    "licitacoes": df_licitacoes,
    "pagamentos_palmas": df_pagamentos,
}
```

As constantes `PASTA_DADOS` e `ARQUIVOS` centralizam a configuração,
evitando caminhos duplicados nos módulos de grafos, heap e hash.

## 4. Pré-processamento

Transformações reutilizáveis são mantidas em
`src/data/preprocessing.py`.

Um exemplo é a conversão de moeda brasileira da dívida ativa:

``` text
3.264,31 -> 3264.31
1.326,00 -> 1326.00
487,56   -> 487.56
```

A separação permite que `loader.py` seja responsável pela leitura e que
as regras de transformação permaneçam independentes e reutilizáveis.

## 5. Estruturas de dados

As três estruturas principais estão organizadas em:

``` text
src/structures/
├── grafo.py
├── heap.py
└── hash_index.py
```

### 5.1 Grafos

Os grafos são implementados com **NetworkX**. A função
`criar_grafo_hierarquico()` recebe um DataFrame, as colunas que formam a
hierarquia, os tipos dos nós e um limite de registros.

Os identificadores dos nós são construídos a partir do caminho
hierárquico para reduzir colisões entre valores iguais em contextos
diferentes.

Exemplos:

``` text
LICITAÇÕES
Órgão
  └── Modalidade
        └── Processo
```

``` text
CONTRATOS
Órgão
  └── Licitação
        └── Contrato
              └── Contratado
```

``` text
PAGAMENTOS
Unidade
  └── Fornecedor
        └── Processo
              └── Empenho
```

A mesma implementação é reutilizada em bases diferentes, alterando
somente `colunas` e `tipos`.

#### Complexidade

Para `n` registros e `k` níveis, uma estimativa conservadora da
implementação atual é:

``` text
O(n * k²)
```

Como `k` é pequeno e fixo nos casos utilizados, o comportamento prático
em relação a `n` aproxima-se de `O(n)`. O armazenamento do grafo depende
de vértices e arestas: `O(V + E)`.

### 5.2 Heap --- fila de prioridade

A fila de prioridade utiliza o módulo nativo `heapq`.

O caso aplicado é a dívida ativa. A fonte disponível contém nome, valor
total da dívida e data da inscrição. Como ela **não fornece variáveis
suficientes para calcular um índice de recuperabilidade**, o protótipo
não cria um score artificial: utiliza o **valor total da dívida** como
critério objetivo de prioridade.

Como `heapq` implementa min-heap, o valor é armazenado negativamente:

``` python
(-prioridade, identificador, data)
```

Assim, o maior valor é removido primeiro.

  Operação                                      Complexidade
  ------------------------------------------- --------------
  `heappush`                                        O(log n)
  Consulta ao topo                                      O(1)
  `heappop`                                         O(log n)
  Construção atual por inserções sucessivas       O(n log n)
  Memória                                               O(n)

O critério representa uma **priorização financeira experimental**, e não
probabilidade de recuperação do crédito.

### 5.3 Tabela hash

A indexação hash utiliza o `dict` nativo do Python:

``` python
{
    chave: [registro_1, registro_2, ...]
}
```

A lista é necessária porque uma chave pode possuir vários registros.

Exemplos:

``` text
chave_contrato -> contratos
cpf_cnpj       -> pagamentos
chave_empenho  -> despesas
chave          -> licitações
```

  Operação       Complexidade média
  ------------ --------------------
  Construção                   O(n)
  Inserção                     O(1)
  Busca                        O(1)
  Memória                      O(n)

`O(1)` representa o caso médio; colisões podem degradar o desempenho no
pior caso.

## 6. Relações entre bases

O CPF/CNPJ permite estabelecer uma das relações mais relevantes:

``` text
CONTRATOS
    |
    | contratado / CNPJ
    v
FORNECEDOR
    ^
    | CPF/CNPJ
    |
PAGAMENTOS
```

O campo `contratados` de contratos possui conteúdo JSON e pode conter
mais de um contratado. Portanto, contrato e fornecedor devem admitir uma
relação muitos-para-muitos no modelo relacional.

Também existem referências entre licitações, contratos e despesas.
Entretanto, a análise das chaves mostrou que nem todas as referências
possuem correspondência direta na base de licitações. Assim, essas
associações não devem ser obrigatórias sem validação e normalização
prévias.

## 7. Persistência relacional

A persistência é baseada em **PostgreSQL/Supabase**, com normalização
até a **Terceira Forma Normal (3FN)**.

Modelo lógico proposto:

``` text
ÓRGÃO
  |
  +----< LICITAÇÃO
  |         |
  |         +----< CONTRATO
  |                   |
  |                   +----< CONTRATO_FORNECEDOR >---- FORNECEDOR
  |
  +----< PAGAMENTO >------------------------------- FORNECEDOR
  |
  +----< RECEITA
  |
  +----< SERVIDOR
             |
             +----< FOLHA_PAGAMENTO
```

O banco deve persistir dados tratados, reduzir redundâncias, aplicar
integridade referencial, permitir consultas SQL e servir como fonte
estruturada para etapas posteriores.

## 8. Separação de responsabilidades

``` text
src/
├── data/
│   ├── loader.py
│   └── preprocessing.py
├── structures/
│   ├── grafo.py
│   ├── heap.py
│   └── hash_index.py
├── database/
│   ├── connection.py
│   └── repository.py
├── tools/
└── agent/
```

Fluxo:

``` text
loader
  ↓
preprocessing
  ↓
structures
  ↓
database
  ↓
tools
  ↓
agent
```

Essa divisão evita misturar carregamento, transformação, estruturas,
persistência e regras do agente no mesmo módulo.

## 9. Testes e validação

As estruturas são demonstradas e validadas separadamente:

``` text
tests/
├── test_grafo.py
├── test_heap.py
└── test_hash.py
```

Os testes verificam criação e reutilização dos grafos, nós e arestas,
criação e remoção de prioridades do heap, criação de índices hash,
buscas e múltiplos registros associados à mesma chave.

A separação dos scripts de teste evita que importar um módulo de
`src/structures` provoque automaticamente carregamento das bases ou
abertura de visualizações.

## 10. Evolução prevista para a Sprint 3

Na Sprint 2 os dados permanecem em CSV. O carregamento repetido das
bases maiores aumenta o tempo de inicialização. Para a Sprint 3 está
prevista uma camada intermediária em **Parquet**:

``` text
data/
├── raw/
│   └── *.csv
└── processed/
    └── *.parquet
```

Fluxo planejado:

``` text
CSV bruto
   ↓
pré-processamento
   ↓
Parquet tratado
   ↓
análise / banco / agente
```

Os CSVs continuarão preservados para rastreabilidade. O Parquet deverá
reduzir o custo de leitura, preservar melhor os tipos e evitar
transformações repetitivas.

## 11. Segurança e integridade

A arquitetura adota como diretrizes:

-   preservar os dados brutos;
-   não criar informações inexistentes nas fontes;
-   documentar transformações;
-   validar relacionamentos antes de criar chaves estrangeiras;
-   evitar exposição desnecessária de dados pessoais;
-   utilizar HTTPS em integrações externas;
-   manter credenciais fora do código-fonte;
-   utilizar variáveis de ambiente para segredos.

CPF/CNPJ deve ser utilizado apenas quando necessário para identificação
técnica e relacionamento entre registros, observando minimização e
proteção dos dados.

## 12. Síntese

``` text
DADOS PÚBLICOS
      ↓
CSV BRUTO
      ↓
LOADER
      ↓
PRÉ-PROCESSAMENTO
      ↓
DATAFRAMES
      ↓
+----------+----------+----------+
|  GRAFO   |   HEAP   |   HASH   |
+----------+----------+----------+
      ↓
BANCO RELACIONAL
      ↓
FERRAMENTAS ANALÍTICAS
      ↓
AGENTE DE IA
```

As responsabilidades são distintas:

-   **grafo:** representar relações entre entidades;
-   **heap:** priorizar registros;
-   **hash:** recuperar registros rapidamente por chave;
-   **banco relacional:** persistir dados, garantir integridade e
    permitir consultas estruturadas.

A arquitetura da Sprint 2 estabelece uma base modular para a evolução do
projeto, permitindo que as próximas etapas avancem para persistência,
integração, análises e construção do agente sem concentrar todas as
responsabilidades em uma única camada.
