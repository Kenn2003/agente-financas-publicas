# Agente Inteligente para Análise da Gestão Financeira Municipal

Projeto Integrador desenvolvido com o objetivo de analisar dados públicos da Prefeitura de Palmas, incluindo informações de receitas, despesas, contratos, licitações e servidores.

A solução será desenvolvida em Python e deverá evoluir para uma aplicação capaz de gerar indicadores financeiros, identificar situações atípicas e permitir consultas em linguagem natural por meio de um agente de Inteligência Artificial.

## Status

Projeto em fase inicial de estruturação — Sprint 1.

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