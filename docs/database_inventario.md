\# Inventário dos Dados para o Banco



\## 1. Objetivo



Este documento registra as estruturas, tipos, nulos, duplicidades,

informações sensíveis e possíveis problemas de qualidade dos arquivos

Parquet produzidos pelo pipeline ETL.



Os arquivos analisados estão localizados em `data/ready/`.



\## 2. Arquivos analisados



| Arquivo | Registros | Colunas | Duplicidades completas |

|---|---:|---:|---:|

| arrecadacao.parquet | 3.542 | 29 | 0 |

| folha\_pagamento.parquet | 489.378 | 30 | 5.018 |

| gastos\_diretos.parquet | 344.323 | 38 | 0 |

| receitas\_recentes.parquet | 103.768 | 12 | 0 |



\## 3. Arrecadação



Arquivo: `data/ready/arrecadacao.parquet`



\### Características



\- 3.542 registros;

\- 29 colunas;

\- nenhuma coluna com valores nulos;

\- nenhum registro totalmente duplicado;

\- período observado: 2010 a 2018, conforme diagnóstico;

\- contém códigos e descrições de receitas;

\- contém valores mensais e anuais;

\- contém informações de atualização dos dados.



\### Possíveis chaves



O campo `id` possui 3.542 valores distintos no diagnóstico e pode ser

candidato a identificador técnico. A confirmação como chave primária

deverá ocorrer durante a carga no banco.



\### Observações



\- `dia`, `mes` e `ano` estão armazenados como texto;

\- existem valores financeiros negativos;

\- há possíveis problemas de codificação de caracteres nas descrições;

\- os campos mensais podem representar valores derivados ou acumulados e

&#x20; precisam ser compreendidos antes de consultas analíticas.



\## 4. Folha de pagamento



Arquivo: `data/ready/folha\_pagamento.parquet`



\### Características



\- 489.378 registros;

\- 30 colunas;

\- 5.018 registros totalmente duplicados;

\- possui valores nulos em campos funcionais, secretariais e financeiros;

\- possui nomes de servidores e matrículas;

\- possui informações remuneratórias;

\- possui datas de admissão e desligamento.



\### Dados que exigem proteção



\- `servidor`;

\- `matricula`;

\- `data\_admissao`;

\- `data\_desligamento`;

\- `localizacao`;

\- valores de remuneração;

\- informações de vínculo e função.



\### Decisão provisória



A exclusão dos registros duplicados ainda não foi realizada. É necessário

verificar se eles são duplicidades reais ou registros legítimos repetidos

em diferentes períodos de referência.



A interface pública do MVP não deverá exibir nomes, matrículas ou outros

dados pessoais individualizados sem justificativa documentada.



\## 5. Gastos diretos



Arquivo: `data/ready/gastos\_diretos.parquet`



\### Características



\- 344.323 registros;

\- 38 colunas;

\- nenhum registro totalmente duplicado;

\- nulos em `data\_liquidacao`, `data\_pagamento` e `historico`;

\- contém informações de empenho, liquidação e pagamento;

\- contém fornecedor e CPF/CNPJ;

\- contém valores financeiros e datas de execução.



\### Dados que exigem proteção ou minimização



\- `cpf\_cnpj`;

\- `fornecedor`, quando associado a pessoa física;

\- informações que possam permitir identificação direta de pessoas.



\### Decisão provisória



O campo `cpf\_cnpj` não deverá ser exibido na interface do MVP.

Para análises agregadas, deverá ser substituído por identificador

pseudonimizado ou removido quando não for necessário.



\## 6. Receitas recentes



Arquivo: `data/ready/receitas\_recentes.parquet`



\### Características



\- 103.768 registros;

\- 12 colunas;

\- nenhuma coluna com valores nulos;

\- nenhum registro totalmente duplicado;

\- dados organizados por órgão, código, ano e mês;

\- contém valores orçados e arrecadados;

\- possui dados entre 2019 e 2024, conforme diagnóstico.



\### Observações



\- `ano`, `mes`, `total`, `orgao` e `covid` estão armazenados como texto;

\- `valor\_orcado` está representado como inteiro;

\- há valores negativos em valores orçados e arrecadados;

\- a interpretação dos valores negativos deve ser validada com a fonte

&#x20; original ou com a documentação do ETL.



\## 7. Problemas de qualidade identificados



\### 7.1 Codificação de caracteres



Foram observados textos corrompidos, por exemplo:



\- `PR╙PRIO`;

\- `HABITA╟├O`;

\- `EDUCA╟├O`;

\- `TRANSFER╩NCIAS`.



Não será feita correção manual antes de identificar a origem do problema.

A codificação deve ser verificada na etapa de leitura, transformação ou

exportação dos dados.



\### 7.2 Valores negativos



Existem valores negativos em campos financeiros. Eles podem representar,

por exemplo, estornos, anulações, ajustes contábeis ou inconsistências.



Nenhum valor negativo será removido automaticamente.



\### 7.3 Datas



Há datas muito antigas e datas de atualização posteriores ao período

de referência dos registros. Esses campos devem ser diferenciados no

modelo:



\- data do fato ou evento;

\- período de referência;

\- data de atualização da fonte.



\### 7.4 Duplicidades na folha



Os 5.018 registros duplicados da folha precisam ser investigados antes

da definição da carga definitiva.



\## 8. Limitações para o projeto de inadimplência



Os arquivos analisados não apresentam, de forma confirmada, campos

individualizados de:



\- dívida ativa;

\- contribuinte tributário;

\- situação de pagamento;

\- data de vencimento;

\- data de quitação;

\- inadimplência;

\- recuperabilidade;

\- beneficiário do IPTU Social.



Consequentemente, ainda não é possível afirmar que os dados disponíveis

sejam suficientes para treinar um modelo supervisionado de predição de

inadimplência.



Até que novas fontes sejam confirmadas, o projeto poderá precisar:



1\. obter uma fonte oficial adicional com dados tributários adequados; ou

2\. redefinir o problema para análise e previsão de arrecadação agregada;

3\. utilizar um protótipo demonstrativo com dados simulados, deixando isso

&#x20;  explicitamente documentado.



\## 9. Diretriz de privacidade



O banco deverá aplicar minimização de dados. Dados pessoais identificáveis

não deverão ser armazenados ou exibidos quando não forem necessários para

o objetivo acadêmico.



CPF, CNPJ, nomes, matrículas e identificadores equivalentes não deverão

ser publicados no repositório Git.



\## 10. Situação atual



\- \[x] Arquivos Parquet localizados;

\- \[x] Quantidade de registros identificada;

\- \[x] Colunas e tipos identificados;

\- \[x] Nulos identificados;

\- \[x] Duplicidades identificadas;

\- \[ ] Investigar codificação dos textos;

\- \[ ] Investigar valores negativos;

\- \[ ] Investigar duplicidades da folha;

\- \[ ] Validar possíveis chaves primárias;

\- \[ ] Definir schema SQL;

\- \[ ] Implementar carga no banco;

\- \[ ] Criar consultas SQL;

\- \[ ] Testar persistência.

