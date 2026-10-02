# SPRINT 2: Arquitetura de Dados e Banco

## 1. O que foi feito

Durante a Sprint 2, a equipe trabalhou na construção da arquitetura de dados e do banco de dados do Sistema de Inteligência Tributária.

Foram definidas e implementadas as estruturas de dados previstas para o projeto, incluindo grafos, heap e tabela hash. Também foi elaborado o modelo Entidade-Relacionamento (ER), realizada a implementação do banco de dados, o carregamento de uma amostra de dados e a execução de consultas SQL para validação.

Além disso, foi realizada a documentação da integração com a fonte de dados utilizada pelo projeto, contemplando os aspectos necessários para o acesso e uso seguro das informações.

## 2. Decisões de modelagem

A arquitetura foi organizada de acordo com as necessidades do Sistema de Inteligência Tributária.

Foram utilizadas diferentes estruturas de dados de acordo com sua finalidade: grafos para representar relações entre os dados, heap para apoiar a priorização das informações e tabela hash para facilitar a localização e indexação dos registros.

No banco de dados, as entidades e seus relacionamentos foram organizados por meio do modelo ER, buscando reduzir a repetição de informações, manter os dados organizados e facilitar as consultas e futuras integrações do sistema.

## 3. Divisão do trabalho

A divisão das atividades da Sprint 2 foi realizada entre os cinco integrantes da equipe:

- Kenneth Wanderson Pereira Veras: Arquitetura de dados.

- Karyne Pereira Lima: Modelagem do banco e Diagrama Entidade-Relacionamento (ER).

- Rafael Gonçalves: Implementação do banco, carregamento da amostra de dados e consultas SQL de validação.

- Arthur Oliveira Felipe: E3 integração com a fonte e documentação.

- Matheus Jorge:  Elaboração e organização do relatório “SPRINT2.md”

## 4. Impedimentos e próximos passos

Durante a Sprint 2, os dados brutos foram mantidos em arquivos CSV, preservando as fontes originais utilizadas no projeto.

Como evolução para a Sprint 3, está prevista a criação de uma camada de dados processados em formato Parquet, buscando reduzir o tempo de leitura, preservar os tipos dos dados e melhorar a eficiência das consultas analíticas.

Também será necessário dar continuidade à coleta e integração dos dados, realizar novos testes e ajustar a estrutura desenvolvida conforme as necessidades identificadas nas próximas etapas do projeto.
