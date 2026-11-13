# Agente Inteligente para Análise da Gestão Financeira Municipal

## 1. Sobre o projeto

O Agente Inteligente para Análise da Gestão Financeira Municipal é um Projeto Integrador desenvolvido com o objetivo de analisar dados públicos da Prefeitura de Palmas, no Tocantins.

O projeto reúne informações relacionadas a receitas, despesas, contratos, licitações e servidores públicos, buscando organizar os dados para facilitar análises, identificar padrões e apoiar a compreensão da gestão financeira municipal.

Projeto em desenvolvimento incremental, com documentação e entregas por sprint.

## 2. Tecnologias utilizadas

- **Python:** linguagem principal do projeto.
- **Pandas:** leitura, transformação e análise de dados tabulares.
- **NumPy:** operações numéricas.
- **PostgreSQL / Supabase:** armazenamento e gerenciamento de dados relacionais.
- **NetworkX:** manipulação e análise de grafos.
- **Matplotlib e Plotly:** visualização de dados.
- **Streamlit:** desenvolvimento de interfaces interativas.
- **Psycopg:** conexão entre Python e PostgreSQL.
- **Git e GitHub:** controle de versão e colaboração da equipe.

## 3. Estrutura do projeto

```text
agente-financas-publicas/
├── data/
│   ├── raw/
│   │   └── csv/
│   ├── processed/
│   └── ready/
├── database/
│   ├── schema.sql
│   ├── queries.sql
│   ├── bancorelacional.sql
│   └── consultas_validacao.sql
├── docs/
│   ├── contribuicoes/
│   └── sprint_02/
├── logs/
├── src/
│   ├── data/
│   ├── database/
│   ├── etl/
│   │   ├── etl_sefin.py
│   │   ├── transform.py
│   │   └── validation.py
│   ├── structures/
│   └── main.py
├── tests/
├── .env.example
├── requirements.txt
└── README.md
```

### Organização dos dados

- `data/raw/csv/`: diretório destinado aos arquivos CSV originais utilizados pelo pipeline.
- `data/processed/`: diretório em que o pipeline ETL salva os arquivos CSV tratados.
- `data/ready/`: diretório destinado às bases preparadas para análises posteriores, incluindo arquivos Parquet quando essa etapa estiver implementada.
- `logs/`: armazena os registros de execução e os relatórios de qualidade.

A existência de um diretório não significa que todas as etapas de geração dos dados estejam automatizadas.

## 4. Fluxo de processamento dos dados

O fluxo de processamento documentado nesta etapa é composto pelas seguintes atividades:

1. Obtenção e organização dos dados públicos.
2. Disponibilização dos arquivos CSV de origem.
3. Leitura das bases utilizando Pandas.
4. Transformação e padronização dos dados.
5. Validação da qualidade das bases processadas.
6. Geração dos arquivos CSV tratados.
7. Registro de logs e informações sobre a qualidade dos dados.
8. Preparação para futuras integrações com o banco de dados e as ferramentas analíticas.

A geração automatizada dos arquivos Parquet e a integração completa de todas as etapas são melhorias futuras do projeto.

## 5. Requisitos para execução

Para executar o pipeline ETL, é necessário ter:

- Python instalado.
- Git instalado para clonar o repositório.
- Dependências do projeto instaladas.
- Arquivos CSV necessários para o processamento.

As instruções abaixo utilizam o PowerShell no Windows.

### 5.1. Obter o projeto

Caso o repositório ainda não esteja disponível no computador:

```powershell
git clone https://github.com/Kenn2003/agente-financas-publicas.git
cd agente-financas-publicas
```

Se o projeto já estiver clonado, entre na pasta existente e atualize a branch principal:

```powershell
git switch main
git pull origin main
```

### 5.2. Criar um ambiente virtual

Na raiz do projeto, execute:

```powershell
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5.3. Instalar as dependências

Com o ambiente virtual ativado, execute:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

O arquivo `requirements.txt` reúne as principais bibliotecas utilizadas pelo projeto.

## 6. Preparação dos arquivos de entrada

O pipeline localizado em `src/etl/etl_sefin.py` espera encontrar os seguintes arquivos:

| Base | Arquivo esperado |
|---|---|
| Arrecadação histórica | `historico_arrecadacao.csv` |
| Gastos diretos históricos | `historico_gastos_diretos.csv` |
| Folha de pagamento histórica | `historico_folha_pagamento.csv` |
| Receitas recentes | `atual_receitas.csv` |

Os arquivos devem estar no diretório:

```text
data/raw/csv/
```

O pipeline lê os arquivos em formato CSV, utilizando vírgula como separador e codificação UTF-8 com suporte a BOM.

Os arquivos de origem precisam corresponder às bases esperadas pelo sistema. O nome do arquivo, a estrutura das colunas e o conteúdo devem ser compatíveis com as transformações implementadas.

**Importante:** o pipeline registra arquivos ausentes como pendências de processamento. Para obter resultados completos, é necessário disponibilizar as bases de entrada esperadas.

## 7. Como executar o pipeline ETL

Na raiz do repositório, execute:

```powershell
python -m src.etl.etl_sefin
```

Esse comando solicita o processamento de todas as bases cadastradas no pipeline.

Para processar somente uma base, utilize o argumento `--base`.

Arrecadação:

```powershell
python -m src.etl.etl_sefin --base arrecadacao
```

Gastos diretos:

```powershell
python -m src.etl.etl_sefin --base gastos_diretos
```

Folha de pagamento:

```powershell
python -m src.etl.etl_sefin --base folha_pagamento
```

Receitas recentes:

```powershell
python -m src.etl.etl_sefin --base receitas_recentes
```

### 7.1. Resultados da execução

Quando o processamento é realizado com sucesso, os arquivos CSV tratados são salvos em `data/processed/`:

- `arrecadacao.csv`
- `gastos_diretos.csv`
- `folha_pagamento.csv`
- `receitas_recentes.csv`

Os registros de execução são gravados em `logs/`, e o relatório da execução mais recente é armazenado em:

```text
logs/qualidade_ultima_execucao.json
```

O relatório registra o status das bases, os caminhos dos arquivos processados, as transformações realizadas e os indicadores de qualidade disponíveis.

Se algum arquivo estiver ausente ou ocorrer um erro durante o processamento, a ocorrência será registrada. Ao final, o comando retorna um código de erro quando alguma base solicitada não é processada com sucesso.

## 8. Transformações e validações

As transformações estão implementadas em `src/etl/transform.py`.

Entre as operações realizadas estão:

- Remoção de espaços no início e no final dos nomes das colunas.
- Remoção de colunas totalmente vazias.
- Conversão de determinadas colunas financeiras para valores numéricos.
- Conversão de colunas identificadas como datas.
- Contabilização de conversões inválidas.

O tratamento numérico considera a presença de vírgula decimal para interpretar valores no padrão brasileiro. Os valores que não puderem ser convertidos são contabilizados como inválidos, em vez de serem substituídos silenciosamente por valores estimados.

As regras de validação estão implementadas em `src/etl/validation.py`, que verifica:

- Se a base está vazia.
- Se existem nomes de colunas duplicados.
- A quantidade de linhas e colunas.
- A quantidade de registros integralmente duplicados.
- A quantidade de valores nulos por coluna.

Essas verificações ajudam a identificar problemas nas bases antes de sua utilização nas análises posteriores.

## 9. Banco de dados e consultas SQL

Os arquivos SQL ficam no diretório `database/`.

Entre os principais arquivos estão:

- `schema.sql`: definição do esquema relacional.
- `queries.sql`: consultas SQL utilizadas no projeto.
- `bancorelacional.sql`: arquivo relacionado à implementação do banco relacional.
- `consultas_validacao.sql`: consultas para verificar os dados armazenados.

A execução do pipeline ETL descrito neste documento não realiza automaticamente a carga relacional dessas quatro bases. A integração com o banco de dados depende dos scripts e procedimentos específicos da etapa de persistência.

## 10. Configuração do banco de dados

O arquivo `.env.example` apresenta um modelo de configuração:

```text
Dados públicos municipais
          ↓
       CSV bruto
          ↓
   Carregamento (Pandas)
          ↓
    Pré-processamento
          ↓
       DataFrames
          ↓
 ┌────────┬────────┬────────┐
 │ Grafo  │  Heap  │  Hash  │
 └────────┴────────┴────────┘
          ↓
   Banco Relacional
 PostgreSQL / Supabase
          ↓
 Ferramentas Analíticas
          ↓
      Agente de IA
```

## Sprint 4 — Modelagem e MVP

### Entregáveis de Arthur

- `notebooks/sprint04_modelagem.ipynb`: notebook autocontido com limpeza, EDA, criação das features e alvos de demonstração, split temporal, treino dos baselines e modelos finais, avaliação e serialização.
- `models/baseline.joblib`: Regressão Logística e Árvore de Decisão como baselines.
- `models/inadimplencia.joblib`: Random Forest ajustada por busca com validação cruzada temporal.
- `models/recuperabilidade.joblib`: classificador das faixas de recuperabilidade.

### Limitação dos rótulos

O arquivo `relatorio_dívida_ativa.csv` contém valor e data de inscrição, mas não possui histórico observado de pagamento, inadimplência ou recuperação. Por isso, os rótulos usados são **proxies sintéticos**, definidos por regras explícitas e uma semente fixa. As métricas demonstram o funcionamento do pipeline; não medem desempenho real e não devem orientar cobrança de contribuintes. A coluna `Nome` é descartada e não é usada como feature.

O split é cronológico: treino até 30/04/2026, validação de 01/05 a 30/06/2026 e teste após 30/06/2026. A validação cruzada para selecionar hiperparâmetros ocorre somente dentro do treino. As métricas por faixas de valor e idade também usam rótulos sintéticos.

### Abrir e executar o notebook

Na raiz do repositório, instale as dependências que não estão no `requirements.txt` e abra `notebooks/sprint04_modelagem.ipynb` no Jupyter ou no VS Code:

```powershell
python -m pip install scikit-learn joblib
```

Execute as células na ordem. O notebook lê `relatorio_dívida_ativa.csv` e grava os três modelos em `models/`.

### Carregar um modelo no MVP

Os arquivos `.joblib` são dicionários; o estimador final fica na chave `estimator`. A interface deve preparar as mesmas features, sem nome ou identificador:

```python
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

pacote = joblib.load(Path("models") / "inadimplencia.joblib")
data_referencia = pd.Timestamp(pacote["data_referencia"])
entrada = pd.DataFrame([{
    "log_valor_divida": np.log1p(valor_divida),
    "idade_divida_dias": max(0, (data_referencia - data_inscricao).days),
}])[pacote["features"]]
probabilidade_proxy = pacote["estimator"].predict_proba(entrada)[0, 1]
```

`probabilidade_proxy` serve apenas para demonstração acadêmica enquanto não houver rótulos observados.
