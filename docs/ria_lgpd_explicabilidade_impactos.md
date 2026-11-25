# Relatório de Impacto Algorítmico — LGPD, Explicabilidade e Impactos Sociais

**Projeto:** Sistema de Inteligência Tributária — Palmas/TO
**Instituição:** Universidade Federal do Tocantins (UFT)
**Curso:** Bacharelado Interdisciplinar em Inteligência Artificial
**Responsável:** Matheus Jorge
**Sprint:** 05 — Governança e Ética
**Data:** 24/11/2026

---

## 1. Escopo desta seção

Este documento compõe o Relatório de Impacto Algorítmico (RIA) da Sprint 05 e abrange três frentes:

1. mapeamento do tratamento de dados pessoais e aspectos de conformidade com a LGPD;
2. explicabilidade dos modelos de Machine Learning e das regras determinísticas de governança;
3. análise de impactos sociais, riscos e recomendações de uso responsável.

A análise possui caráter acadêmico e experimental. Não constitui parecer jurídico, autorização administrativa para cobrança tributária nem validação dos modelos para uso operacional.

Os modelos utilizados na Sprint 04 possuem variáveis-alvo sintéticas e não observadas. Portanto, seus resultados não representam probabilidades validadas de inadimplência ou recuperabilidade real.

---

# 2. Mapeamento de dados pessoais e LGPD

## 2.1. Princípios aplicáveis

O tratamento de dados pessoais no projeto deve observar, entre outros, os princípios de:

- finalidade;
- adequação;
- necessidade;
- livre acesso;
- qualidade dos dados;
- transparência;
- segurança;
- prevenção;
- não discriminação;
- responsabilização e prestação de contas.

No contexto do Poder Público, qualquer tratamento operacional futuro deverá estar vinculado a finalidade pública legítima, específica, explícita e informada, bem como a competência ou atribuição legal do órgão responsável.

A definição da base legal definitiva depende de validação jurídica da Prefeitura de Palmas e não é estabelecida por este protótipo acadêmico.

---

## 2.2. Inventário dos principais conjuntos de dados

### Dívida ativa

O arquivo `relatorio_dívida_ativa.csv` contém:

- `Nome`;
- `Valor Total da Dívida`;
- `Data da Inscrição`.

O nome permite identificação direta do titular e, portanto, constitui dado pessoal.

O coletor `src/data/collectors/divida_ativa.py` recebe da API de origem os seguintes campos:

- nome;
- CPF/CNPJ;
- data da inscrição;
- valor total.

O CSV consolidado utilizado pela camada analítica não mantém CPF/CNPJ, reduzindo a quantidade de identificadores diretos na saída.

Entretanto, os dados brutos de origem podem conter identificadores pessoais e exigem proteção proporcional ao risco.

### Folha de pagamento

A base `data/ready/folha_pagamento.parquet` contém, entre outras variáveis:

- matrícula;
- nome do servidor;
- setor;
- cargo;
- função;
- vínculo;
- secretaria;
- datas de admissão e desligamento;
- localização;
- vencimentos;
- descontos;
- valores de rendimento.

Essa base contém dados pessoais identificáveis e informações econômico-funcionais.

Esses dados não fazem parte das features utilizadas pelos modelos de inadimplência e recuperabilidade analisados neste RIA.

### Gastos diretos

A base `data/ready/gastos_diretos.parquet` contém, entre outros campos:

- CPF/CNPJ;
- fornecedor;
- processo;
- empenho;
- liquidação;
- datas de pagamento;
- valores financeiros;
- histórico.

Quando o fornecedor é pessoa física, o CPF constitui identificador direto.

Essa base também não é utilizada como entrada dos modelos de dívida ativa analisados nesta seção.

### Arrecadação e receitas

As bases:

- `data/ready/arrecadacao.parquet`;
- `data/ready/receitas_recentes.parquet`;

apresentam predominantemente informações financeiras, contábeis e agregadas, sem identificadores pessoais diretos aparentes nas colunas atualmente disponíveis.

---

## 2.3. Minimização na camada de Machine Learning

O processo da Sprint 04 descarta nomes e outros identificadores antes da modelagem.

Os modelos versionados utilizam apenas duas features:

- `log_valor_divida`;
- `idade_divida_dias`.

Assim, nome, CPF/CNPJ, matrícula, servidor e outros identificadores diretos não são utilizados como variáveis preditoras.

Essa escolha reduz o tratamento de dados pessoais na camada de ML e está alinhada ao princípio da necessidade.

Entretanto, a minimização no modelo não torna todo o sistema anônimo, pois identificadores ainda podem existir nas fontes e etapas anteriores do pipeline.

---

## 2.4. Dados sensíveis e IPTU Social

A base analítica atual de dívida ativa não permite determinar individualmente a elegibilidade ao IPTU Social.

A camada de governança implementada na Sprint 05 prevê proteção para situações envolvendo idosos, aposentados, pensionistas e pessoas com deficiência, conforme as regras administrativas implementadas.

A informação relativa à deficiência pode revelar condição de saúde e deve receber proteção reforçada caso seja futuramente tratada de forma individualizada.

Nenhum indicador territorial pode ser utilizado como substituto para informações administrativas individuais de renda, idade, deficiência ou elegibilidade.

---

## 2.5. Armazenamento e versionamento

Foram identificados dados pessoais em arquivos utilizados pelo projeto, inclusive no arquivo `relatorio_dívida_ativa.csv`, que está versionado no repositório Git.

O versionamento cria um risco adicional: a exclusão de um arquivo da versão atual não necessariamente remove o conteúdo de versões históricas.

Para eventual utilização operacional recomenda-se:

- evitar versionamento de bases identificáveis;
- utilizar armazenamento segregado e protegido;
- implementar controle de acesso por perfil;
- registrar acessos e operações relevantes;
- utilizar pseudonimização ou anonimização quando compatível com a finalidade;
- armazenar no repositório apenas estruturas, exemplos sintéticos e artefatos estritamente necessários.

---

## 2.6. Retenção

O protótipo atual não define política formal de retenção dos dados pessoais.

Antes de qualquer uso administrativo deverão ser definidos:

- prazo de retenção;
- critérios de arquivamento;
- hipóteses de conservação legal;
- processo de descarte seguro;
- tratamento das cópias de segurança;
- procedimento aplicável ao histórico de versionamento.

Os dados não devem ser mantidos indefinidamente apenas por conveniência técnica.

---

## 2.7. Segurança e integridade das fontes

A metodologia geoespacial utiliza dados públicos provenientes do IBGE e do GeoPalmas.

Durante a etapa experimental, a obtenção de dados do GeoPalmas apresentou problema de validação TLS, tendo sido realizado acesso diagnóstico sem validação do certificado.

Por esse motivo, os dados resultantes dessa coleta não devem ser considerados fonte criptograficamente autenticada para uso oficial até que o processamento seja repetido com cadeia de certificados válida.

---

## 2.8. Bases legais a verificar

A definição da base legal não deve ser feita apenas pela equipe técnica.

Em uma eventual implantação pela Administração Pública, deverão ser avaliadas pela área jurídica, entre outras hipóteses pertinentes:

- cumprimento de obrigação legal ou regulatória;
- execução de políticas públicas;
- exercício das competências legais e atribuições do serviço público;
- regras específicas aplicáveis ao tratamento de dados sensíveis, quando presentes.

A escolha deve ser vinculada à finalidade concreta de cada operação e documentada pelo controlador.

---

# 3. Explicabilidade

## 3.1. Abordagem em duas camadas

A explicabilidade do sistema foi separada em duas camadas:

1. explicabilidade dos modelos de Machine Learning;
2. explicabilidade das regras determinísticas de governança.

Essa separação é necessária porque as decisões dos modelos experimentais e as decisões de proteção administrativa possuem naturezas diferentes.

---

## 3.2. Modelos analisados

Foram analisados os artefatos versionados:

- `models/inadimplencia.joblib`;
- `models/recuperabilidade.joblib`.

Ambos utilizam `RandomForestClassifier`.

### Inadimplência proxy

Features utilizadas:

- `log_valor_divida`;
- `idade_divida_dias`.

Status do target:

`sintetico_proxy_nao_observado`.

O artefato registra explicitamente que não deve ser utilizado para decisões reais, pois a base não contém resultados observados de pagamento, inadimplência ou recuperação.

### Recuperabilidade proxy

O modelo classifica os registros em:

- `baixa`;
- `media`;
- `alta`.

Também utiliza somente:

- `log_valor_divida`;
- `idade_divida_dias`.

O target também é sintético e não observado.

---

## 3.3. Técnica de interpretabilidade

Foi utilizada a técnica `Feature Importance` dos modelos Random Forest.

Ela representa a relevância global de cada variável para o comportamento do modelo.

É importante destacar que Feature Importance:

- não demonstra causalidade;
- não representa contribuição local exata para uma previsão individual;
- não permite afirmar que determinada porcentagem de uma previsão específica foi causada por uma feature;
- deve ser interpretada como explicabilidade global do modelo.

---

## 3.4. Importância global das variáveis

### Modelo de inadimplência proxy

| Feature | Importância |
|---|---:|
| `log_valor_divida` | 90,13% |
| `idade_divida_dias` | 9,87% |

O modelo depende predominantemente do valor transformado da dívida.

Essa concentração deve ser interpretada juntamente com a limitação metodológica do experimento, pois o próprio alvo sintético foi construído com influência de valor e tempo da dívida.

### Modelo de recuperabilidade proxy

| Feature | Importância |
|---|---:|
| `log_valor_divida` | 73,75% |
| `idade_divida_dias` | 26,25% |

Novamente, o valor da dívida possui maior importância global.

Como a classe sintética de recuperabilidade foi construída a partir das mesmas dimensões, a importância encontrada não comprova capacidade de previsão de recuperação financeira real.

---

## 3.5. Exemplo real desidentificado

Foi executada uma previsão utilizando um registro real pertencente ao conjunto temporal de teste da Sprint 04.

Nenhum nome, CPF/CNPJ ou identificador pessoal foi utilizado ou registrado na evidência.

Entradas fornecidas ao modelo:

- `log_valor_divida = 6,2088`;
- `idade_divida_dias = 83`.

### Resultado — inadimplência proxy

Classe prevista:

`0`

Probabilidades:

- classe 0: `65,25%`;
- classe 1: `34,75%`.

Esses valores não significam que o contribuinte tenha 34,75% de chance real de inadimplência.

Eles representam apenas a saída do modelo experimental treinado com target sintético.

### Resultado — recuperabilidade proxy

Classe prevista:

`media`

Probabilidades:

- alta: `0,62%`;
- baixa: `0,68%`;
- média: `98,70%`.

Da mesma forma, esses valores não podem ser interpretados como probabilidade real de recuperação.

A evidência reproduzível está disponível em:

- `docs/evidencias/explicabilidade/exemplo_real_anonimizado.json`;
- `docs/evidencias/explicabilidade/exemplo_real_anonimizado.md`.

O script utilizado para geração é:

- `src/analysis/explicabilidade_ria.py`.

---

## 3.6. Explicabilidade da governança determinística

Além da explicação do ML, a Sprint 05 implementou uma camada determinística de proteção ao IPTU Social.

A política de governança pode produzir três estados:

- `bloquear`;
- `revisao_humana`;
- `prosseguir_demais_controles`.

A decisão pode ser acompanhada do motivo da decisão e da regra administrativa correspondente.

Quando os dados são insuficientes, inválidos ou não verificados, o sistema adota política `fail-closed`, encaminhando o caso para revisão humana.

O estado `prosseguir_demais_controles` não significa autorização automática de cobrança.

Essa arquitetura oferece uma explicação mais direta e auditável do que a saída probabilística do modelo de ML.

---

## 3.7. Direito à explicação e revisão

Em eventual utilização administrativa, a explicação fornecida ao cidadão não deve se limitar a uma probabilidade ou score.

Deve ser possível informar, de forma clara:

- quais dados foram utilizados;
- qual finalidade justificou o tratamento;
- quais critérios relevantes influenciaram o resultado;
- quais regras de governança foram aplicadas;
- qual foi o resultado produzido;
- quais limitações existem;
- como solicitar revisão humana;
- como contestar dados incorretos ou desatualizados.

Nenhuma decisão com potencial de produzir efeito prejudicial deve depender exclusivamente dos modelos experimentais atualmente disponíveis.

---

# 4. Impactos sociais e recomendações

## 4.1. Uso de targets sintéticos

O principal risco metodológico do sistema é a ausência de rótulos observados de inadimplência, pagamento e recuperação.

Os targets da Sprint 04 foram produzidos artificialmente para demonstrar o pipeline de ML.

Consequentemente:

- métricas elevadas não comprovam desempenho operacional;
- diferenças entre grupos não comprovam discriminação real;
- probabilidades produzidas pelo modelo não são estimativas administrativas validadas;
- o modelo não deve priorizar cobranças reais.

A utilização operacional depende da obtenção de dados históricos de desfecho e de nova validação.

---

## 4.2. Risco de falso positivo

Um falso positivo de inadimplência poderia levar um contribuinte regular ou de menor risco a receber prioridade indevida em uma política de cobrança.

Possíveis consequências:

- cobrança desnecessária;
- aumento de custos administrativos;
- constrangimento;
- tratamento desigual;
- redução da confiança no serviço público.

Mitigação:

- revisão humana;
- validação em fontes oficiais;
- possibilidade de contestação;
- proibição de ação automática baseada exclusivamente no modelo.

---

## 4.3. Risco para grupos vulneráveis

Uma política de cobrança automatizada pode produzir impacto desproporcional sobre pessoas economicamente vulneráveis.

Por esse motivo, a camada de proteção ao IPTU Social deve ser aplicada independentemente do score de ML.

Benefícios oficialmente reconhecidos resultam em bloqueio.

Casos com informação insuficiente ou elegibilidade indeterminada devem ser encaminhados para revisão humana.

---

## 4.4. Desigualdade territorial

A análise geoespacial demonstrou heterogeneidade socioeconômica entre áreas de Palmas.

Foram consolidados:

- 733 setores censitários;
- 280 áreas municipais;
- 1.624 fragmentos de interseção;
- 244 áreas com indicador de rendimento;
- 179 áreas classificadas com suporte analítico alto ou moderado.

Esses indicadores servem apenas como contexto territorial exploratório.

---

## 4.5. Falácia ecológica

Um dos maiores riscos é inferir características individuais a partir de médias territoriais.

Uma área com rendimento médio baixo não permite concluir que um determinado contribuinte possui baixa renda.

Da mesma forma, uma área de maior renda não comprova capacidade individual de pagamento.

Utilizar esse tipo de inferência para priorizar cobrança configuraria risco de falácia ecológica e possível discriminação por proxy.

Portanto, indicadores territoriais:

- não devem determinar renda individual;
- não devem determinar elegibilidade ao IPTU Social;
- não devem ser utilizados como feature individual de cobrança;
- não devem substituir dados administrativos oficiais.

---

## 4.6. Qualidade e cobertura dos dados territoriais

A cobertura territorial do GeoPalmas utilizado não corresponde à totalidade do município.

Também existem:

- setores sem população;
- setores povoados sem indicador de rendimento;
- aproximações de interpolação areal;
- sobreposições geométricas residuais;
- diferença temporal entre Censo 2022 e contexto operacional de 2026.

Ausência de informação não deve ser transformada automaticamente em valor zero nem interpretada como ausência de vulnerabilidade.

---

## 4.7. Risco de discriminação por proxy

Mesmo quando atributos protegidos não são fornecidos diretamente ao modelo, outras variáveis podem funcionar como proxies.

No modelo atual, a quantidade de features é reduzida e não há uso de dados territoriais.

Caso localização, renda territorial ou outras variáveis sejam adicionadas futuramente, deverá ser realizada nova avaliação de fairness e impacto social antes de qualquer implantação.

---

## 4.8. Automação excessiva

O uso de inteligência artificial em cobrança tributária possui potencial de afetar economicamente cidadãos.

Por esse motivo, a automação não deve eliminar a responsabilidade administrativa nem transformar uma previsão estatística em decisão jurídica automática.

O modelo deve apoiar análise, não substituir:

- verificação oficial;
- competência administrativa;
- decisão motivada;
- revisão humana;
- direito de contestação.

---

## 4.9. Transparência

Os cidadãos afetados por eventual sistema operacional devem receber informação acessível sobre:

- existência de tratamento automatizado;
- finalidade;
- categorias de dados utilizadas;
- critérios gerais do sistema;
- limitações;
- existência de revisão humana;
- canal de contestação e correção.

Informações técnicas protegidas por segredo comercial ou de segurança podem exigir tratamento específico, sem eliminar o dever de transparência aplicável.

---

## 4.10. Recomendações para uso responsável

Antes de eventual implantação operacional recomenda-se:

1. obter histórico real de pagamentos, inadimplência e recuperação;
2. retreinar e validar os modelos com targets observados;
3. realizar nova análise de fairness com grupos adequadamente definidos;
4. manter a proteção ao IPTU Social independente do modelo de ML;
5. validar juridicamente as regras administrativas e bases legais;
6. remover identificadores desnecessários das camadas analíticas;
7. evitar versionamento de dados pessoais identificáveis;
8. estabelecer política formal de retenção e descarte;
9. implementar controle de acesso e trilhas de auditoria;
10. utilizar criptografia em trânsito e armazenamento quando aplicável;
11. validar a autenticidade das fontes externas;
12. implementar monitoramento de desempenho, drift e disparidades;
13. assegurar revisão humana antes de qualquer ação prejudicial;
14. estabelecer canal de explicação, correção e contestação;
15. realizar novo RIA sempre que houver mudança relevante de dados, modelo ou finalidade.

---

# 5. Conclusão

O protótipo apresenta medidas relevantes de governança, incluindo minimização de dados na camada de Machine Learning, explicabilidade global por Feature Importance, exemplo reproduzível desidentificado e proteção determinística ao IPTU Social.

Entretanto, permanecem limitações fundamentais.

Os modelos utilizam targets sintéticos e não podem ser interpretados como preditores validados de inadimplência ou recuperabilidade reais.

O sistema também possui dados pessoais em camadas de origem e em arquivos do repositório, o que exige controles adicionais de armazenamento, acesso, retenção e versionamento.

Os indicadores geoespaciais são adequados apenas como contexto exploratório e não devem ser convertidos em atributos individuais de capacidade econômica ou elegibilidade.

Assim, qualquer adoção administrativa futura deve permanecer condicionada a validação jurídica, dados de desfecho reais, revisão humana, transparência, segurança e mecanismos efetivos de contestação.

---

## Referências técnicas e normativas

- Lei nº 13.709/2018 — Lei Geral de Proteção de Dados Pessoais (LGPD).
- Autoridade Nacional de Proteção de Dados — Guia Orientativo: Tratamento de Dados Pessoais pelo Poder Público.
- `docs/protecao_iptu_social.md`.
- `docs/metodologia_geoespacial.md`.
- `notebooks/sprint04_modelagem.ipynb`.
- `models/inadimplencia.joblib`.
- `models/recuperabilidade.joblib`.
- `docs/evidencias/explicabilidade/exemplo_real_anonimizado.md`.
