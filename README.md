# Agente Inteligente para Análise da Gestão Financeira Municipal

Projeto Integrador desenvolvido com o objetivo de analisar dados públicos da Prefeitura de Palmas, incluindo informações de receitas, despesas, contratos, licitações e servidores.

A solução será desenvolvida em Python e deverá evoluir para uma aplicação capaz de gerar indicadores financeiros, identificar situações atípicas e permitir consultas em linguagem natural por meio de um agente de Inteligência Artificial.

## Status

Projeto em desenvolvimento incremental, com documentação e entregas por sprint.

## Sprint 2 — Arquitetura de Dados e Banco de Dados

Na Sprint 2, o projeto avançou da organização inicial das bases públicas para a construção de uma arquitetura de dados modular, com foco em **estruturas de dados, modelagem relacional, persistência e preparação para as futuras ferramentas do agente de IA**.

### Arquitetura de dados

O fluxo atual do projeto foi organizado da seguinte forma:

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
