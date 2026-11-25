# Agente Inteligente para Análise da Gestão Financeira Municipal

## 1. Sobre o projeto

O Agente Inteligente para Análise da Gestão Financeira Municipal é um Projeto Integrador desenvolvido com o objetivo de analisar dados públicos da Prefeitura de Palmas, no Tocantins.

O projeto reúne informações relacionadas a receitas, despesas, contratos, licitações e servidores públicos, buscando organizar os dados para facilitar análises, identificar padrões e apoiar a compreensão da gestão financeira municipal.

O projeto está em desenvolvimento incremental, com documentação e entregas organizadas por sprint. Os modelos de inadimplência e recuperabilidade são demonstrações acadêmicas baseadas em rótulos sintéticos; não devem orientar ações de cobrança nem decisões sobre contribuintes.

## 2. Tecnologias utilizadas

- **Python:** linguagem principal do projeto.
- **Pandas:** leitura, transformação e análise de dados tabulares.
- **NumPy:** operações numéricas.
- **PostgreSQL / Supabase:** armazenamento e gerenciamento de dados relacionais.
- **Psycopg:** conexão entre Python e PostgreSQL.
- **NetworkX:** manipulação e análise de grafos.
- **Matplotlib e Plotly:** visualização de dados.
- **Streamlit:** desenvolvimento de interfaces interativas.
- **Scikit-learn e Joblib:** treinamento, avaliação e serialização dos modelos demonstrativos.
- **Git e GitHub:** controle de versão e colaboração da equipe.

As dependências Python do projeto estão relacionadas em `requirements.txt`. Algumas funcionalidades também dependem de configurações e arquivos de dados locais.

## 3. Estrutura do projeto

A estrutura abaixo apresenta os principais diretórios e arquivos do projeto; alguns arquivos podem variar conforme a sprint e a configuração local.

```text
agente-financas-publicas/
├── app/                       # Interface Streamlit
│   ├── components/            # Componentes da interface
│   ├── pages/                 # Páginas do aplicativo
│   └── streamlit_app.py       # Entrada da aplicação
├── data/
│   ├── raw/                   # Dados de origem
│   ├── processed/             # Dados processados
│   └── ready/                 # Bases preparadas para análise
├── database/                  # Schema e consultas SQL
├── docs/                      # Documentação e evidências
│   ├── contribuicoes/
│   ├── evidencias/
│   ├── mapas/
│   ├── requisitos/
│   ├── sprint_02/
│   └── uml/
├── logs/                      # Registros de execução, quando gerados
├── models/                    # Artefatos dos modelos demonstrativos
├── notebooks/                 # Notebooks de modelagem e fairness
├── src/
│   ├── agents/                # Agentes e ferramentas
│   ├── data/                  # Carregamento e preparação de dados
│   ├── database/              # Acesso ao banco de dados
│   ├── etl/                   # Pipeline ETL
│   ├── governance/            # Regras de proteção e governança
│   ├── ml/                    # Código de modelagem
│   └── structures/            # Estruturas de dados
├── tests/                     # Testes automatizados
├── .env.example               # Exemplo de configuração local
├── requirements.txt           # Dependências Python
└── README.md
```

### Organização dos dados

- `data/raw/`: arquivos de origem utilizados pelos fluxos de processamento.
- `data/processed/`: arquivos produzidos pelo pipeline ETL.
- `data/ready/`: bases preparadas para análises posteriores, incluindo arquivos Parquet disponíveis no projeto.
- `logs/`: diretório destinado a registros e relatórios de execução, quando gerados.
- `docs/`: documentação, relatórios e evidências das sprints.
- `models/`: artefatos serializados usados nas demonstrações de modelagem.
- `notebooks/`: notebooks de modelagem e análise.
- `tests/`: testes automatizados do projeto.

A presença de um diretório não significa que todas as etapas de geração, carga ou atualização dos dados estejam automatizadas.

## 4. Fluxo de processamento dos dados

O fluxo de processamento documentado para o projeto inclui as seguintes atividades:

1. Obtenção e organização dos dados públicos.
2. Disponibilização dos arquivos de origem necessários.
3. Leitura das bases utilizando Pandas.
4. Transformação e padronização dos dados.
5. Validação da qualidade das bases processadas.
6. Geração de arquivos tratados pelo pipeline ETL.
7. Registro de logs e informações sobre a qualidade dos dados, quando aplicável.
8. Preparação dos dados para integração com o banco de dados e as ferramentas analíticas.

Os arquivos Parquet disponíveis em `data/ready/` são utilizados por análises e funcionalidades que dependem dessas bases. A geração ou atualização de cada arquivo depende do fluxo correspondente e dos dados de entrada disponíveis localmente.

## 5. Requisitos para execução

Para executar o pipeline ETL ou a aplicação, é necessário ter:

- Python instalado.
- Git instalado para clonar o repositório.
- Dependências do projeto instaladas.
- Os arquivos de dados exigidos pela funcionalidade que será executada.
- Configurações locais preenchidas quando uma funcionalidade depender de banco de dados ou serviço externo.

As instruções abaixo incluem comandos para Windows (PowerShell) e Linux/macOS. Execute-os na raiz do repositório.

### 5.1. Obter o projeto

Caso o repositório ainda não esteja disponível no computador:

```bash
git clone https://github.com/Kenn2003/agente-financas-publicas.git
cd agente-financas-publicas
```

Se o projeto já estiver clonado, atualize a branch principal:

```bash
git switch main
git pull --ff-only origin main
```

Se houver alterações locais pendentes, revise-as e guarde-as antes de atualizar a branch, para evitar conflitos ou perda de trabalho.

### 5.2. Criar e ativar um ambiente virtual

#### Windows — PowerShell

Na raiz do projeto, execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Linux/macOS

Na raiz do projeto, execute:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 5.3. Instalar as dependências

Com o ambiente virtual ativado, execute:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

O arquivo `requirements.txt` reúne as dependências Python registradas para o projeto. Funcionalidades específicas podem exigir arquivos de dados ou configurações locais adicionais.

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

**Importante:** arquivos ausentes podem impedir o processamento de uma ou mais bases. Para obter resultados completos, disponibilize os arquivos de entrada exigidos pelo fluxo que será executado.

Não versione arquivos de dados pessoais, credenciais, chaves ou outros dados protegidos. Verifique as regras do projeto e a origem dos dados antes de compartilhar ou adicionar arquivos ao repositório.

## 7. Como executar o pipeline ETL

Na raiz do repositório, com o ambiente virtual ativado, execute:

```bash
python -m src.etl.etl_sefin
```

Esse comando solicita o processamento das bases cadastradas no pipeline.

Para processar somente uma base, utilize o argumento `--base`.

Arrecadação:

```bash
python -m src.etl.etl_sefin --base arrecadacao
```

Gastos diretos:

```bash
python -m src.etl.etl_sefin --base gastos_diretos
```

Folha de pagamento:

```bash
python -m src.etl.etl_sefin --base folha_pagamento
```

Receitas recentes:

```bash
python -m src.etl.etl_sefin --base receitas_recentes
```

### 7.1. Resultados da execução

Quando o processamento é realizado com sucesso, os arquivos CSV tratados são salvos em `data/processed/`:

- `arrecadacao.csv`
- `gastos_diretos.csv`
- `folha_pagamento.csv`
- `receitas_recentes.csv`

Os registros de execução são gravados em `logs/`, e o relatório da execução mais recente pode ser armazenado em:

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

A execução do pipeline ETL descrito neste documento não realiza automaticamente a carga relacional das bases. A integração com o banco de dados depende dos scripts e procedimentos específicos da etapa de persistência.

Para detalhes sobre as bases, tabelas, validações e procedimentos documentados, consulte [docs/database_inventario.md](docs/database_inventario.md).

## 10. Configuração local e visão geral da arquitetura

O arquivo `.env.example` apresenta um modelo de configuração local, quando aplicável. Crie sua configuração local a partir desse exemplo e preencha somente os valores necessários para o ambiente utilizado.

**Não inclua no repositório o arquivo `.env`, senhas, tokens ou chaves de API.** Confira também se o `.gitignore` impede o versionamento de arquivos locais com credenciais.

O fluxo conceitual do projeto é:

```text
Dados públicos municipais
          ↓
       CSV bruto
          ↓
   Carregamento e processamento
          ↓
       Dados tratados
          ↓
 Banco de dados e estruturas
          ↓
 Interface e agentes de análise
```

A execução de cada etapa depende dos arquivos de dados, das configurações e dos procedimentos correspondentes.

## 11. Executar a demonstração Streamlit

Com o ambiente virtual ativado e as dependências instaladas, execute na raiz do repositório:

```bash
streamlit run app/streamlit_app.py
```

O aplicativo pode depender de arquivos de dados locais e, nas funcionalidades que carregam modelos, dos artefatos disponíveis em `models/`.

A demonstração de inadimplência e recuperabilidade utiliza alvos sintéticos. Seus resultados não representam pagamentos, inadimplência ou recuperação observados e não devem orientar cobrança ou decisões sobre contribuintes.

## 12. Sprint 4 — Modelagem e MVP

### Entregáveis de Arthur

- `notebooks/sprint04_modelagem.ipynb`: notebook autocontido com limpeza, análise exploratória, criação das features e alvos de demonstração, divisão temporal, treinamento dos baselines e modelos finais, avaliação e serialização.
- `models/baseline.joblib`: baselines de Regressão Logística e Árvore de Decisão.
- `models/inadimplencia.joblib`: modelo Random Forest de inadimplência proxy.
- `models/recuperabilidade.joblib`: classificador das faixas de recuperabilidade proxy.

### Limitação dos rótulos

O arquivo `relatorio_dívida_ativa.csv` contém valor e data de inscrição, mas não possui histórico observado de pagamento, inadimplência ou recuperação. Por isso, os rótulos usados são **proxies sintéticos**, definidos por regras explícitas e uma semente fixa.

As métricas demonstram o funcionamento do pipeline; não medem desempenho real e não devem orientar cobrança de contribuintes. A coluna `Nome` é descartada e não é usada como feature.

O split é cronológico: treino até 30/04/2026, validação de 01/05 a 30/06/2026 e teste após 30/06/2026. A validação cruzada para selecionar hiperparâmetros ocorre somente dentro do treino. As métricas por faixas de valor e idade também usam rótulos sintéticos.

### Abrir e executar o notebook

Com o ambiente virtual ativado e as dependências instaladas pelo `requirements.txt`, abra `notebooks/sprint04_modelagem.ipynb` no Jupyter ou no VS Code.

Execute as células na ordem. O notebook depende do arquivo local `relatorio_dívida_ativa.csv` e grava os modelos em `models/`. A disponibilidade e o uso desse arquivo devem respeitar as regras de privacidade e segurança do projeto.

### Carregar um modelo no MVP

Os arquivos `.joblib` são dicionários; o estimador final fica na chave `estimator`. A interface deve preparar as mesmas features registradas no artefato, sem nome ou identificador:

```python
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

pacote = joblib.load(Path("models") / "inadimplencia.joblib")
data_referencia = pd.Timestamp(pacote["data_referencia"])

entrada = pd.DataFrame([{
    "log_valor_divida": np.log1p(valor_divida),
    "idade_divida_dias": max(
        0,
        (data_referencia - pd.Timestamp(data_inscricao)).days,
    ),
}])[pacote["features"]]

estimador = pacote["estimator"]
probabilidades = estimador.predict_proba(entrada)[0]
classes = list(estimador.classes_)

if 1 not in classes:
    raise ValueError("O modelo não contém a classe sintética positiva 1.")

probabilidade_proxy = probabilidades[classes.index(1)]
```

`probabilidade_proxy` serve apenas para demonstração acadêmica enquanto não houver rótulos observados.


## 13. Sprint 5 — Governança, fairness e portfólio

A Sprint 5 reúne entregáveis de governança, análise de fairness, proteção ao IPTU Social, impactos e documentação.

- **Kenneth — IPTU Social:** regra de proteção contra a seleção de beneficiários protegidos para ações preditivas de cobrança, com testes automatizados.
- **Karyne — Portfólio e entrega:** organização da documentação, revisão de links, atualização do README, índice do portfólio e checklist de entrega.
- **Arthur — Model Card:** documentação da finalidade, dos dados, das métricas, das limitações, dos riscos, dos usos proibidos e dos mecanismos de contestação dos modelos da Sprint 4.
- **Rafael — Fairness:** análise de paridade demográfica e igualdade de oportunidade, com resultados, limitações e recomendações de mitigação.
- **Matheus — RIA:** documentação de LGPD, explicabilidade e impactos sociais.

### Documentação e evidências da Sprint 5

- **Portfólio e checklist de entrega:** [Índice do portfólio](docs/README.md) · [Checklist da Sprint 5](docs/checklist_entrega.md)
- [Model Card](docs/model_card.md)
- [Proteção ao IPTU Social](docs/protecao_iptu_social.md)
- [RIA — Fairness](docs/ria_fairness.md)
- [RIA — LGPD, explicabilidade e impactos sociais](docs/ria_lgpd_explicabilidade_impactos.md)
- [Notebook de fairness](notebooks/sprint05_fairness.ipynb)
- [Testes do IPTU Social](tests/test_iptu_social.py)
- [Testes de integração do IPTU Social](tests/test_integracao_iptu_social.py)
- [Testes de fairness](tests/test_fairness.py)
- [Evidência de explicabilidade](docs/evidencias/explicabilidade/exemplo_real_anonimizado.md)
- [Relatório de testes do IPTU Social](docs/evidencias/relatorio_testes_iptu_social.txt)
- [Relatório de testes de fairness](docs/evidencias/fairness/relatorio_testes.txt)

A aplicação das regras de proteção ao IPTU Social não substitui análise jurídica ou administrativa. Resultados de fairness dependem dos dados, dos atributos disponíveis e dos rótulos utilizados; limitações e interpretações estão descritas nos relatórios correspondentes.

## 14. Documentação de sprints anteriores

- [Sprint 2 — Arquitetura de Dados e Banco](docs/sprint_02/SPRINT2.md)
- [Arquitetura de dados](docs/sprint_02/arquitetura-dados.md)
- [Inventário dos dados e validação do banco](docs/database_inventario.md)
- [Metodologia geoespacial](docs/metodologia_geoespacial.md)
- [Requisitos](docs/requisitos/README.md)

## 15. Uso responsável e limitações

Os dados, indicadores, modelos e documentos devem ser interpretados dentro do escopo e das limitações descritas em cada entrega.

Em particular:

- Modelos treinados com alvos sintéticos são demonstrações acadêmicas e não previsões de resultados reais.
- Métricas calculadas sobre alvos sintéticos não comprovam desempenho em situações reais.
- Análises territoriais agregadas não permitem concluir características individuais de moradores ou contribuintes.
- Nenhum score demonstrativo deve ser usado isoladamente para cobrança, concessão de benefícios ou decisões sobre pessoas.
- A adoção administrativa de qualquer sistema depende de validação dos dados e do modelo, revisão humana, avaliação jurídica, transparência, segurança e mecanismos efetivos de contestação.