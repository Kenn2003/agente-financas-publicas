# Agente Inteligente para Análise da Gestão Financeira Municipal

## 1. Sobre o projeto

O Agente Inteligente para Análise da Gestão Financeira Municipal é um Projeto Integrador desenvolvido com o objetivo de analisar dados públicos da Prefeitura de Palmas, no Tocantins.

O projeto reúne informações relacionadas a receitas, despesas, contratos, licitações e servidores públicos, buscando organizar os dados para facilitar análises, identificar padrões e apoiar a compreensão da gestão financeira municipal.

A solução utiliza Python para processamento e análise de dados, estruturas de dados, armazenamento relacional e ferramentas que poderão apoiar futuras consultas por meio de Inteligência Artificial.

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
DB_HOST=localhost
DB_PORT=5432
DB_NAME=agente_financas_publicas
DB_USER=postgres
DB_PASSWORD=coloque_sua_senha_local_aqui
```

Os valores devem ser ajustados conforme a configuração do banco utilizado.

O arquivo de exemplo não configura automaticamente as variáveis de ambiente. Cada script deve estar preparado para ler essas variáveis ou carregar o arquivo de ambiente.

Nunca publique senhas, tokens ou credenciais reais no GitHub. O arquivo `.env` com dados sensíveis deve permanecer fora do controle de versão.

## 11. Geração dos arquivos Parquet: etapa futura

A geração automatizada dos arquivos Parquet ainda não foi implementada integralmente no fluxo atual do projeto.

Embora exista o diretório `data/ready/` e tenham sido incluídos arquivos Parquet no repositório, os scripts responsáveis por gerar esses arquivos a partir do fluxo atual ainda precisam ser desenvolvidos e integrados.

Essa etapa foi adiada porque o processamento das bases pode consumir uma quantidade significativa de memória RAM, dependendo do volume de dados. Sua implementação deverá considerar estratégias para reduzir o consumo de memória e permitir o processamento de forma mais eficiente.

**A geração dos arquivos Parquet não é obrigatória para a entrega atual.** O foco desta etapa está no pipeline de processamento CSV, nas transformações e nas validações implementadas. A criação automatizada dos Parquets será tratada como uma melhoria futura, sem impedir a continuidade das demais atividades do projeto.

Portanto, os arquivos Parquet atualmente presentes no repositório não devem ser interpretados como evidência de que sua geração automatizada e reproduzível já está concluída.

## 12. Organização e responsabilidades da equipe

A divisão de responsabilidades da Sprint 3 está organizada da seguinte forma:

| Integrante | Responsabilidade |
|---|---|
| Responsável pela coleta automatizada | Coleta automatizada dos dados |
| Matheus | Enriquecimento dos dados com informações do IBGE |
| Kenneth | Implementação do pipeline ETL |
| Karyne | Banco de dados e persistência |
| Arthur | Análise exploratória de dados (EDA) e mapa |
| Rafael | Documentação do projeto no README.md |
| Kenneth, na integração final | Integração dos componentes e validação final |

A divisão representa as responsabilidades atribuídas à equipe. O estado de conclusão de cada atividade deve ser confirmado pelos integrantes e pelos registros de commits e pull requests.

## 13. Qualidade, privacidade e uso dos dados

O projeto utiliza dados públicos para fins acadêmicos e analíticos. Mesmo quando os dados são publicamente acessíveis, seu uso deve respeitar a finalidade do projeto e os princípios de segurança, transparência e responsabilidade.

Recomenda-se:

- Preservar os arquivos originais para possibilitar a rastreabilidade das transformações.
- Registrar erros, conversões inválidas e valores ausentes.
- Evitar inferir informações que não estejam presentes nas bases.
- Não divulgar credenciais de acesso ao banco.
- Avaliar a necessidade de restringir ou agregar dados que possam expor informações pessoais.
- Documentar a origem e a data de obtenção de cada base utilizada.
- Interpretar os indicadores considerando a cobertura, a atualização e as limitações dos dados disponíveis.

As fontes oficiais específicas e as datas de extração de cada conjunto de dados devem ser registradas conforme forem confirmadas pela equipe.

## 14. Próximas etapas

Entre as melhorias previstas para o projeto estão:

- Desenvolvimento dos scripts de geração dos arquivos Parquet.
- Otimização do processamento para reduzir o consumo de memória RAM.
- Integração do enriquecimento de dados com informações do IBGE.
- Integração do pipeline com a carga no banco relacional.
- Continuidade das validações de consistência e qualidade.
- Desenvolvimento das análises exploratórias e do mapa.
- Evolução das ferramentas analíticas e da futura interface de consulta.

Essas melhorias serão implementadas de forma incremental, conforme as prioridades e os recursos disponíveis para cada etapa do projeto.

## 15. Considerações finais

O projeto busca transformar dados públicos municipais em informações organizadas e úteis para a análise da gestão financeira. A documentação, o controle de qualidade e a reprodutibilidade são partes essenciais desse processo, permitindo que outros integrantes da equipe e avaliadores compreendam como configurar o ambiente, processar os dados e verificar os resultados.

A documentação reflete o fluxo ETL CSV disponível nesta etapa e identifica explicitamente a geração automatizada dos arquivos Parquet como uma melhoria futura.
