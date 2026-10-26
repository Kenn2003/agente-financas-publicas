# Inventário dos Dados e Validação do Banco

## 1. Objetivo

Este documento registra as estruturas, quantidades, tipos de dados, valores
nulos, duplicidades, tratamentos realizados, informações que exigem proteção,
resultados de validação e limitações dos dados utilizados no projeto.

O inventário considera:

- os arquivos Parquet produzidos pelo pipeline ETL;
- o carregamento realizado no PostgreSQL;
- as validações executadas após a carga;
- as limitações dos dados em relação ao problema de inadimplência e dívida ativa.

Os arquivos Parquet analisados estão localizados em:




data/ready/




O banco utilizado é:



PostgreSQL
Banco: agente_financas_publicas
Porta: 5432




---

## 2. Arquivos de origem

As quantidades desta seção correspondem aos arquivos Parquet antes da carga
definitiva no banco.

| Arquivo | Registros de origem | Colunas | Duplicidades completas |
|---|---:|---:|---:|
| `arrecadacao.parquet` | 3.542 | 29 | 0 |
| `folha_pagamento.parquet` | 489.378 | 30 | 5.018 |
| `gastos_diretos.parquet` | 344.323 | 38 | 0 |
| `receitas_recentes.parquet` | 103.768 | 12 | 0 |

As duplicidades informadas são duplicidades integrais, ou seja, registros com
todos os campos iguais.

---

## 3. Tabelas implementadas

O banco PostgreSQL contém as seguintes tabelas principais:

| Tabela | Finalidade |
|---|---|
| `arrecadacao` | Armazenar dados históricos de arrecadação municipal |
| `folha_pagamento` | Armazenar dados de folha de pagamento |
| `gastos_diretos` | Armazenar dados de empenho, liquidação e pagamento |
| `receitas_recentes` | Armazenar dados recentes de receitas municipais |
| `carga_dados` | Registrar e auditar as cargas realizadas |

Os principais arquivos responsáveis pela camada de banco são:



database/schema.sql
database/queries.sql
src/database/load_parquets.py
src/database/repository.py




---

## 4. Registros carregados no PostgreSQL

Após o processo de carga e os tratamentos definidos, foram registrados os
seguintes quantitativos:

| Tabela | Registros carregados |
|---|---:|
| `arrecadacao` | 3.542 |
| `folha_pagamento` | 484.360 |
| `gastos_diretos` | 344.323 |
| `receitas_recentes` | 103.768 |
| `carga_dados` | 4 registros de auditoria |

A tabela `carga_dados` registrou quatro cargas com sucesso:

| Arquivo | Tabela de destino | Registros | Sucesso |
|---|---|---:|---|
| `arrecadacao.parquet` | `arrecadacao` | 3.542 | Sim |
| `folha_pagamento.parquet` | `folha_pagamento` | 484.360 | Sim |
| `gastos_diretos.parquet` | `gastos_diretos` | 344.323 | Sim |
| `receitas_recentes.parquet` | `receitas_recentes` | 103.768 | Sim |

A folha de pagamento possuía 489.378 registros no arquivo de origem.
Foram identificadas 5.018 duplicidades integrais e carregados 484.360
registros no banco.

O arquivo Parquet original não foi alterado.

---

## 5. Arrecadação

Arquivo de origem:




data/ready/arrecadacao.parquet




### 5.1 Características

- 3.542 registros;
- 29 colunas;
- nenhuma coluna com valores nulos no diagnóstico inicial;
- nenhum registro totalmente duplicado;
- período observado entre 2010 e 2018;
- presença de códigos e descrições de receitas;
- presença de valores mensais e anuais;
- presença de informações de atualização dos dados.

### 5.2 Identificador

O campo `id` apresentou 3.542 valores distintos no arquivo analisado.

Na tabela carregada, não foram encontrados IDs duplicados na verificação
realizada.

Esse campo é utilizado como identificador técnico no modelo atual. A
interpretação definitiva como chave de negócio depende da documentação da
fonte original.

### 5.3 Observações

- Os campos `dia`, `mes` e `ano` estão armazenados como texto.
- Existem valores financeiros negativos.
- Os valores negativos não foram removidos automaticamente.
- Os campos mensais podem representar valores derivados, acumulados ou
  lançamentos individuais.
- A interpretação contábil dos valores deve ser validada com a documentação
  oficial da fonte.

---

## 6. Folha de pagamento

Arquivo de origem:




data/ready/folha_pagamento.parquet




### 6.1 Características

- 489.378 registros no arquivo de origem;
- 30 colunas;
- 5.018 duplicidades integrais;
- 484.360 registros carregados no banco;
- presença de valores nulos em campos funcionais, secretariais e financeiros;
- presença de nomes de servidores e matrículas;
- presença de informações remuneratórias;
- presença de datas de admissão e desligamento.

### 6.2 Tratamento das duplicidades

As duplicidades integrais foram removidas durante a carga no banco, conforme
a regra definida no processo de carregamento.

O arquivo Parquet original foi preservado sem alterações.

A diferença observada foi:




489.378 registros de origem
- 5.018 duplicidades integrais
= 484.360 registros carregados




### 6.3 Dados que exigem proteção

Os seguintes campos podem conter dados pessoais ou informações que exigem
controle de acesso e minimização:

- `servidor`;
- `matricula`;
- `data_admissao`;
- `data_desligamento`;
- `localizacao`;
- valores de remuneração;
- informações de vínculo;
- informações de função.

A interface pública do MVP não deve exibir nomes, matrículas ou outros dados
pessoais individualizados sem justificativa documentada.

Os dados pessoais não devem ser publicados no repositório Git.

---

## 7. Gastos diretos

Arquivo de origem:



data/ready/gastos_diretos.parquet




### 7.1 Características

- 344.323 registros;
- 38 colunas;
- nenhum registro totalmente duplicado;
- presença de valores nulos em `data_liquidacao`;
- presença de valores nulos em `data_pagamento`;
- presença de valores nulos em `historico`;
- informações de empenho, liquidação e pagamento;
- presença de fornecedor e CPF/CNPJ;
- presença de valores financeiros e datas de execução.

### 7.2 Tratamento das datas

Durante a carga, valores sentinela correspondentes à data:



0001-01-01




foram convertidos para `NULL` no campo `data_liquidacao`.

Validação realizada:



datas_sentinela = 0




Após o tratamento, foram encontrados:



data_liquidacao IS NULL = 19.909 registros




Esses valores nulos devem ser interpretados como ausência de uma data de
liquidação válida ou como informação não registrada. Eles não devem ser
interpretados como datas reais.

### 7.3 Dados que exigem proteção ou minimização

Os seguintes campos exigem atenção:

- `cpf_cnpj`;
- `fornecedor`, quando associado a pessoa física;
- informações que permitam a identificação direta ou indireta de pessoas.

O campo `cpf_cnpj` não deve ser exibido na interface do MVP.

Para análises agregadas, o identificador deve ser removido ou substituído por
uma representação pseudonimizada, somente quando houver necessidade
justificada.

---

## 8. Receitas recentes

Arquivo de origem:



data/ready/receitas_recentes.parquet




### 8.1 Características

- 103.768 registros;
- 12 colunas;
- nenhuma coluna com valores nulos no diagnóstico inicial;
- nenhum registro totalmente duplicado;
- dados organizados por órgão, código, ano e mês;
- presença de valores orçados e arrecadados;
- período observado entre 2019 e 2024.

### 8.2 Observações

- Os campos `ano`, `mes`, `total`, `orgao` e `covid` estão armazenados como
  texto.
- O campo `valor_orcado` está representado como inteiro.
- Existem valores negativos em campos financeiros.
- Os valores negativos não foram removidos automaticamente.
- A interpretação desses valores deve ser validada com a fonte original ou
  com a documentação do processo ETL.

---

## 9. Problemas e decisões de qualidade

### 9.1 Codificação de caracteres

Inicialmente, alguns caracteres acentuados foram exibidos incorretamente no
terminal `psql`, por exemplo:




IPTU - PR�PRIO




A investigação confirmou que os dados não estavam corrompidos.

Foram realizadas as seguintes verificações:

- o arquivo Parquet contém corretamente o texto `IPTU - PRÓPRIO`;
- o servidor PostgreSQL utiliza `server_encoding = UTF8`;
- os dados armazenados no PostgreSQL estão em UTF-8;
- o cliente `psql` estava utilizando `client_encoding = WIN1252`;
- após configurar o cliente para UTF-8, os caracteres passaram a ser
  exibidos corretamente.

A correção utilizada no PowerShell foi:



$env:PGCLIENTENCODING = "UTF8"




Não foi necessária a recarga dos dados nem a correção manual dos textos.

### 9.2 Valores negativos

Foram identificados valores negativos em campos financeiros de algumas
fontes.

Esses valores podem representar:

- estornos;
- anulações;
- cancelamentos;
- ajustes contábeis;
- devoluções;
- inconsistências na origem.

Nenhum valor negativo foi removido automaticamente. A remoção ou
transformação desses valores somente deve ocorrer após a compreensão da
regra contábil da fonte.

### 9.3 Padronização textual

Foram observadas variações na grafia de nomes de secretarias, incluindo
diferenças de:

- acentuação;
- abreviação;
- espaçamento;
- nomenclatura histórica;
- uso de caracteres especiais.

Exemplos de variações podem incluir nomes com e sem acentos ou alterações
na denominação da secretaria ao longo do tempo.

Essas diferenças não foram alteradas na camada bruta.

Caso seja necessária uma padronização para análise, ela deve ser realizada em
uma camada analítica ou em uma coluna derivada, preservando os valores
originais.

### 9.4 Tipos armazenados como texto

Alguns campos temporais ou categóricos estão armazenados como texto, como
`ano`, `mes`, `dia` e `orgao`.

A conversão para tipos numéricos ou datas deve ser realizada somente após:

1. verificar se todos os valores possuem formato válido;
2. identificar valores ausentes ou inconsistentes;
3. documentar a transformação;
4. manter os dados originais preservados.

---

## 10. Validações realizadas

Foram executadas as seguintes validações:

- contagens das tabelas conferidas;
- quatro cargas registradas na tabela `carga_dados`;
- quatro cargas registradas com `sucesso = true`;
- duplicidades integrais da folha tratadas durante a carga;
- IDs duplicados não encontrados nas tabelas principais verificadas;
- datas sentinela não encontradas após o tratamento;
- consulta de registros com `data_liquidacao IS NULL`;
- execução das consultas de agregação;
- teste do repositório Python;
- validação das funções de consulta do repositório;
- confirmação da leitura correta dos caracteres em UTF-8.

### 10.1 Resultado resumido

| Verificação | Resultado |
|---|---|
| Registros em `arrecadacao` | 3.542 |
| Registros em `folha_pagamento` | 484.360 |
| Registros em `gastos_diretos` | 344.323 |
| Registros em `receitas_recentes` | 103.768 |
| Registros em `carga_dados` | 4 |
| Cargas com sucesso | 4 |
| IDs duplicados nas tabelas verificadas | 0 |
| Datas sentinela em `gastos_diretos` | 0 |
| Datas nulas em `data_liquidacao` | 19.909 |
| Exibição UTF-8 | Corrigida |

---

## 11. Limitações para o projeto de inadimplência

As bases atualmente carregadas contêm dados de:

- arrecadação;
- folha de pagamento;
- gastos diretos;
- receitas recentes.

Entretanto, os dados disponíveis não apresentam, de forma confirmada, campos
individualizados suficientes de:

- dívida ativa;
- contribuinte tributário;
- situação de pagamento;
- data de vencimento;
- data de quitação;
- inadimplência;
- recuperabilidade;
- beneficiário do IPTU Social;
- vínculo individual entre contribuinte, imóvel e débito.

Consequentemente, não é possível afirmar que os dados atuais sejam
suficientes para treinar um modelo supervisionado definitivo de predição
individual de inadimplência ou de recuperabilidade da dívida ativa.

As tabelas atuais podem apoiar:

- análise exploratória de arrecadação;
- análise histórica de receitas;
- análise agregada de gastos;
- análise agregada da folha;
- construção de indicadores financeiros;
- protótipos metodológicos;
- estudos com dados simulados ou agregados.

Até que novas fontes oficiais sejam confirmadas, o projeto poderá:

1. obter uma fonte oficial adicional com dados tributários adequados;
2. redefinir o problema para análise ou previsão de arrecadação agregada;
3. utilizar dados simulados para demonstrar a metodologia;
4. desenvolver um score demonstrativo, deixando explícito que ele não
   representa uma decisão fiscal real.

Não se deve afirmar que o modelo definitivo de inadimplência está pronto
sem uma variável-alvo validada, dados adequados e avaliação experimental.

---

## 12. Diretrizes de privacidade e segurança

O banco e o MVP devem aplicar os princípios de minimização, finalidade,
necessidade, segurança e transparência.

Não devem ser publicados no repositório Git:

- CPF;
- CNPJ quando permitir identificação indevida;
- nomes de servidores;
- matrículas;
- endereços individualizados;
- dados pessoais não anonimizados;
- arquivos Parquet com informações pessoais;
- dumps do banco;
- credenciais;
- arquivos `.env`.

O arquivo `.env` deve permanecer fora do versionamento.

A interface do MVP deve priorizar:

- dados agregados;
- identificadores pseudonimizados;
- regiões amplas;
- indicadores estatísticos;
- valores agrupados;
- ausência de exposição individualizada desnecessária.

O score produzido por eventual modelo deve ser tratado como instrumento de
apoio à análise, e não como:

- prova de fraude;
- prova de irregularidade;
- decisão automática de cobrança;
- justificativa única para sanção;
- substituto da análise humana;
- mecanismo de discriminação de grupos vulneráveis.

---

## 13. Artefatos implementados

A camada de banco possui os seguintes artefatos:



database/schema.sql
database/queries.sql
src/database/load_parquets.py
src/database/repository.py




Também foram disponibilizados scripts auxiliares de inspeção e validação
dentro de `src/database/`.

A documentação relacionada ao banco inclui:



docs/database_inventario.md
docs/sprint_02/arquitetura-dados.md




---

## 14. Execução básica

### 14.1 Criar o schema

A execução do schema deve ser realizada no banco configurado pela equipe:



psql -U postgres -d agente_financas_publicas -f database/schema.sql




### 14.2 Executar a carga

O carregador deve ser executado conforme as instruções presentes no código
e utilizando as variáveis de ambiente configuradas.

Os arquivos de dados devem permanecer em diretórios locais e não devem ser
publicados quando contiverem dados pessoais ou sensíveis.

### 14.3 Executar as consultas



psql -U postgres -d agente_financas_publicas -f database/queries.sql




Para exibir corretamente caracteres acentuados no PowerShell:




$env:PGCLIENTENCODING = "UTF8"




### 14.4 Testar o repositório Python

A conexão Python depende das variáveis de ambiente configuradas no arquivo
`.env`, que não deve ser enviado ao GitHub.

Exemplo de teste:



py -c "from src.database.repository import listar_cargas; print(listar_cargas())"




---

## 15. Situação atual

- [x] Arquivos Parquet localizados;
- [x] Quantidade de registros identificada;
- [x] Colunas e tipos identificados;
- [x] Valores nulos identificados;
- [x] Duplicidades identificadas;
- [x] Duplicidades integrais da folha tratadas durante a carga;
- [x] Arquivo Parquet original preservado;
- [x] Schema SQL implementado;
- [x] Banco PostgreSQL configurado;
- [x] Dados carregados;
- [x] Auditoria de cargas implementada;
- [x] Consultas SQL criadas;
- [x] Repositório Python implementado;
- [x] Persistência testada;
- [x] Contagens finais validadas;
- [x] IDs duplicados verificados nas tabelas principais;
- [x] Datas sentinela verificadas;
- [x] Tratamento de datas inválidas realizado;
- [x] Codificação investigada;
- [x] Exibição UTF-8 corrigida;
- [x] Limitações dos dados documentadas;
- [ ] Investigar semanticamente os valores negativos;
- [ ] Definir eventual padronização analítica dos nomes de secretarias;
- [ ] Confirmar se o diagrama representa exatamente o schema atual;
- [ ] Alinhar com a equipe o padrão definitivo dos diretórios de dados;
- [ ] Confirmar a disponibilidade de dados adequados para a variável-alvo de
  inadimplência.

---

## 16. Conclusão

A camada de banco de dados foi implementada, carregada, testada e
documentada.

O banco PostgreSQL contém dados estruturados de arrecadação, folha de
pagamento, gastos diretos e receitas recentes. As quatro cargas foram
registradas com sucesso e as principais validações foram executadas.

A investigação de codificação confirmou que os dados acentuados estão
armazenados corretamente em UTF-8. A exibição incorreta ocorreu por uma
configuração incompatível do cliente `psql` e foi corrigida sem necessidade
de recarga.

Apesar de os dados serem adequados para análises financeiras e
exploratórias, as bases atualmente disponíveis não comprovam a existência de
informações individuais suficientes para treinar um modelo definitivo de
inadimplência ou de recuperabilidade da dívida ativa.

Qualquer etapa posterior de Machine Learning deve utilizar uma variável-alvo
validada, respeitar as limitações dos dados, proteger informações pessoais,
evitar decisões automáticas e manter supervisão humana.