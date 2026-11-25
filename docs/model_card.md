# Model Card — Modelos de Inadimplência e Recuperabilidade

**Projeto:** Agente Inteligente para Análise da Gestão Financeira Municipal
**Instituição:** Prefeitura Municipal de Palmas — dados públicos
**Versão:** 1.0
**Data:** 25/11/2026
**Responsável pela documentação:** Rafael
**Referência metodológica:** Mitchell et al. (2019), *Model Cards for Model Reporting*.

---

## 1. Visão geral

Este documento descreve os modelos experimentais de classificação de inadimplência e recuperabilidade desenvolvidos no contexto da Sprint 4 do projeto.

Os modelos foram construídos para demonstrar um pipeline de Machine Learning aplicado à análise de dados de dívida ativa municipal.

**Limitação fundamental:** a base utilizada não possui rótulos observados de pagamento, inadimplência ou recuperação. Por esse motivo, foram criados alvos sintéticos para experimentação. Os modelos não devem ser interpretados como instrumentos capazes de prever a situação real de contribuintes.

Os artefatos foram gerados pelo notebook `notebooks/sprint04_modelagem.ipynb` e armazenados em `models/`.

## 2. Identificação dos modelos

### 2.1 Modelo de inadimplência

- **Nome:** Classificador de Inadimplência Proxy.
- **Algoritmo:** Random Forest Classifier.
- **Tipo de tarefa:** classificação binária.
- **Classes:** 0 e 1.
- **Variáveis de entrada:**
  - `log_valor_divida`: logaritmo natural de 1 mais o valor da dívida.
  - `idade_divida_dias`: quantidade de dias entre a inscrição e a data de referência.
- **Número de árvores:** 100.
- **Profundidade máxima:** 8.
- **Mínimo de amostras por folha:** 30.
- **Balanceamento:** `class_weight="balanced"`.
- **Semente aleatória:** 42.
- **Artefato:** `models/inadimplencia.joblib`.

Os hiperparâmetros foram selecionados por busca em grade (`GridSearchCV`), utilizando validação cruzada temporal com três divisões (`TimeSeriesSplit`) e F1-score como critério de seleção.

### 2.2 Modelo de recuperabilidade

- **Nome:** Classificador de Recuperabilidade Proxy.
- **Algoritmo:** Random Forest Classifier.
- **Tipo de tarefa:** classificação multiclasse.
- **Classes:** baixa, média e alta.
- **Variáveis de entrada:**
  - `log_valor_divida`.
  - `idade_divida_dias`.
- **Número de árvores:** 160.
- **Profundidade máxima:** 10.
- **Mínimo de amostras por folha:** 20.
- **Balanceamento:** `class_weight="balanced"`.
- **Semente aleatória:** 42.
- **Artefato:** `models/recuperabilidade.joblib`.

O modelo classifica as faixas de recuperabilidade construídas a partir de um score sintético, e não de resultados financeiros efetivamente observados.

## 3. Finalidade e usos pretendidos

Os modelos foram desenvolvidos exclusivamente para:

- Demonstrar técnicas de classificação aplicadas a dados financeiros municipais.
- Experimentar pipelines de treinamento, validação e teste temporal.
- Avaliar o funcionamento de algoritmos Random Forest.
- Apoiar estudos acadêmicos sobre análise exploratória de dívida ativa.
- Servir como protótipos para futuras pesquisas, condicionadas à obtenção de dados observados e validação adequada.

## 4. Usos não recomendados ou proibidos

Os modelos não devem ser utilizados para:

- Autorizar, determinar ou priorizar cobranças reais.
- Classificar individualmente contribuintes como inadimplentes.
- Restringir direitos ou aplicar sanções administrativas.
- Conceder ou negar benefícios tributários.
- Determinar elegibilidade ao IPTU Social.
- Inferir renda, vulnerabilidade ou condição socioeconômica individual.
- Substituir análise administrativa ou revisão humana.
- Produzir decisões automatizadas com efeitos sobre os direitos dos cidadãos.

As probabilidades e classificações produzidas representam apenas o comportamento dos modelos diante dos alvos artificiais utilizados no treinamento.

## 5. Dados utilizados

### 5.1 Origem

Foi utilizado o arquivo `relatorio_dívida_ativa.csv`, contendo informações relacionadas à dívida ativa municipal.

O notebook realiza a preparação dos dados da seguinte maneira:

1. Remove registros duplicados.
2. Mantém os campos de valor total da dívida e data de inscrição.
3. Descarta a coluna de nome e outros identificadores antes da modelagem.
4. Converte os valores financeiros e as datas.
5. Remove registros inválidos.
6. Calcula a idade da dívida em dias.
7. Calcula o logaritmo do valor da dívida.

A data de referência utilizada na construção das variáveis é 01/10/2026.

### 5.2 Alvos sintéticos

**Inadimplência:**

O alvo binário é gerado por uma probabilidade artificial:

`logit = -3.8 + 0.35 × log_valor_divida + 0.35 × (idade_divida_dias / 365)`

Em seguida, aplica-se a função logística e uma amostragem Bernoulli com semente 42.

**Recuperabilidade:**

O score sintético é calculado por:

`score = 0.65 × exp(-(idade_divida_dias / 365) / 3) + 0.35 × exp(-log_valor_divida / 5)`

O resultado é limitado ao intervalo de 0 a 1 e dividido nas seguintes faixas:

- Baixa: score inferior a 0,65.
- Média: score entre 0,65 e inferior a 0,75.
- Alta: score igual ou superior a 0,75.

Essas regras são artificiais e não representam comportamento real de pagamento ou recuperação.

### 5.3 Limitações dos dados

- Não existem rótulos observados de inadimplência ou recuperação.
- Não há comprovação de que os resultados sintéticos correspondam à realidade financeira dos contribuintes.
- As variáveis utilizadas são limitadas ao valor e à idade da dívida.
- Não há dados suficientes para estabelecer conclusões sobre características individuais dos contribuintes.
- A presença de dados pessoais na base original exige controles específicos de acesso, proteção e retenção.

## 6. Estratégia de treinamento e validação

Foi utilizada uma divisão temporal para evitar que observações futuras fossem utilizadas no treinamento de modelos destinados a avaliar períodos anteriores.

Os limites definidos no notebook foram:

| Conjunto | Período |
|---|---|
| Treinamento | Até 30/04/2026 |
| Validação | 01/05/2026 a 30/06/2026 |
| Teste | Após 30/06/2026 |

Para o modelo de inadimplência, os hiperparâmetros foram selecionados por validação cruzada temporal dentro do conjunto de treinamento. Após a seleção, o modelo final foi ajustado com treinamento e validação combinados.

Para recuperabilidade, o classificador foi treinado inicialmente no conjunto de treinamento e, posteriormente, ajustado com treinamento e validação combinados.

Os resultados de teste apresentados neste documento são métricas experimentais calculadas sobre alvos sintéticos.

## 7. Métricas de desempenho

### 7.1 Inadimplência

**Validação:**

| Métrica | Resultado |
|---|---:|
| Acurácia | 0,6432 |
| Precisão | 0,2404 |
| Recall | 0,6263 |
| F1-score | 0,3474 |

**Teste temporal:**

| Métrica | Resultado |
|---|---:|
| Acurácia | 0,7921 |
| Precisão | 0,3033 |
| Recall | 0,2113 |
| F1-score | 0,2491 |

F1-score da validação cruzada temporal: 0,3706.

### 7.2 Recuperabilidade

| Métrica | Validação | Teste temporal |
|---|---:|---:|
| Acurácia | 0,7608 | 0,9480 |
| F1-score macro | 0,6742 | 0,7773 |

A acurácia elevada na classificação de recuperabilidade deve ser interpretada com cautela, pois as classes foram derivadas de uma fórmula que utiliza as mesmas variáveis fornecidas ao modelo.

### 7.3 Interpretação

As métricas demonstram o funcionamento técnico do pipeline e a capacidade de reproduzir padrões dos alvos sintéticos.

Elas não demonstram desempenho preditivo real, validade operacional ou capacidade de identificar contribuintes efetivamente inadimplentes.

Não devem ser utilizadas como indicadores de qualidade de uma ferramenta de cobrança real.

## 8. Análise exploratória por subgrupos

Foram realizados experimentos de avaliação por faixas de valor e idade da dívida, utilizando os resultados do classificador de inadimplência proxy.

A análise por faixa de valor apresentou os seguintes resultados:

| Grupo | Registros | Taxa de seleção | TPR |
|---|---:|---:|---:|
| Até R$ 500 | 7.296 | 0% | 0% |
| R$ 500 a R$ 5.000 | 3.409 | 29,39% | 34,97% |
| Acima de R$ 5.000 | 343 | 74,05% | 72,03% |

A análise também apresentou uma limitação importante na divisão por idade da dívida: o grupo de até 30 dias contém apenas dois registros, quantidade insuficiente para conclusões estatísticas confiáveis.

**Interpretação e limitações:**

- Existem diferenças expressivas entre as faixas de valor.
- Os resultados são calculados sobre rótulos sintéticos.
- Faixa de valor da dívida não equivale a faixa de renda.
- Idade da dívida representa tempo desde a inscrição, e não idade do contribuinte.
- Não há vinculação individual entre os contribuintes e os indicadores territoriais do Censo.
- Não é possível afirmar que os resultados comprovam discriminação ou ausência de discriminação.

Os experimentos não constituem comprovação de paridade demográfica ou igualdade de oportunidade entre grupos socioeconômicos reais.

## 9. Limitações, riscos e considerações éticas

### 9.1 Risco de interpretação indevida

As previsões podem ser confundidas com avaliações reais de inadimplência ou capacidade de recuperação, embora sejam baseadas em alvos artificiais.

### 9.2 Risco de discriminação

Diferenças de classificação entre faixas de valor podem refletir as regras utilizadas para produzir os alvos sintéticos. Não representam necessariamente diferenças reais de comportamento dos contribuintes.

### 9.3 Risco de automação excessiva

A utilização das classificações para orientar cobranças sem revisão humana poderia gerar consequências administrativas indevidas.

### 9.4 Risco de inferência territorial

Indicadores territoriais representam características agregadas de setores censitários e não podem ser utilizados para inferir renda, vulnerabilidade ou elegibilidade de uma pessoa específica.

### 9.5 Proteção de dados

Embora os identificadores sejam descartados antes da modelagem, a base original contém informações pessoais. O descarte de identificadores no pipeline não elimina a necessidade de proteção dos arquivos de origem, controle de acesso e política de retenção.

## 10. Governança e relação com o IPTU Social

A proteção relacionada ao IPTU Social foi implementada em uma camada determinística e independente das previsões de Machine Learning.

A política de governança contempla três situações:

- `bloquear`: benefício reconhecido, impedindo o prosseguimento da cobrança.
- `revisao_humana`: informações ausentes, inválidas, não verificadas ou situação indeterminada.
- `prosseguir_demais_controles`: situação verificada sem reconhecimento de benefício, permitindo apenas a continuidade das demais verificações administrativas.

A última situação não representa autorização automática de cobrança.

Os modelos de Machine Learning não participam da determinação de elegibilidade ao IPTU Social.

A implementação foi submetida a 106 testes automatizados, todos aprovados. Os módulos `iptu_social.py` e `controle_cobranca.py` apresentaram 100% de cobertura de instruções e desvios nos testes reportados. Essa cobertura é restrita aos módulos avaliados e não comprova, isoladamente, segurança ou conformidade jurídica integral.

A validação jurídica definitiva e a integração com sistemas administrativos reais permanecem pendentes.

## 11. Recomendações para uso futuro

Antes de qualquer utilização operacional, recomenda-se:

1. Obter dados históricos reais de pagamento, inadimplência e recuperação.
2. Construir rótulos observados e documentar sua origem.
3. Realizar novo treinamento e validação temporal.
4. Avaliar desempenho por grupos socioeconômicos com dados adequados e legalmente autorizados.
5. Investigar disparidades entre grupos e possíveis variáveis proxy.
6. Implementar monitoramento de desempenho e mudanças nos dados.
7. Garantir revisão humana e possibilidade de contestação.
8. Aplicar minimização de dados, controle de acesso, segurança e retenção.
9. Submeter o tratamento de dados e as finalidades à avaliação jurídica e de proteção de dados.
10. Manter a camada determinística de proteção do IPTU Social independente dos modelos.

## 12. Transparência e contestação

O projeto deve garantir que qualquer utilização futura de sistemas automatizados que possa afetar direitos dos titulares seja acompanhada de transparência, explicação adequada e possibilidade de revisão, observando especialmente o artigo 20 da LGPD, quando aplicável.

Nenhuma decisão administrativa individual deve ser justificada exclusivamente por uma classificação produzida por estes modelos experimentais.

**Canal de contato:** não definido nesta etapa experimental. Antes de qualquer implantação operacional, a administração municipal deverá estabelecer e divulgar um canal oficial para solicitações de explicação, correção de dados e contestação de resultados.

## 13. Rastreabilidade e reprodução

A origem dos artefatos foi identificada no notebook:

`notebooks/sprint04_modelagem.ipynb`

Commit de inclusão:

`6628cf0 — Adiciona entregáveis da Sprint 4`

Artefatos:

- `models/baseline.joblib`
- `models/inadimplencia.joblib`
- `models/recuperabilidade.joblib`

O notebook registra a metodologia, as variáveis, as regras de geração dos alvos, os parâmetros e o processo de gravação dos modelos.

Os metadados dos artefatos registram o ambiente de treinamento:

- Python 3.12.14.
- pandas 2.2.3.
- scikit-learn 1.8.0.

A reprodução deve considerar as versões originais das dependências. O carregamento em versões diferentes do scikit-learn pode gerar avisos de incompatibilidade.

As saídas originais das células de treinamento não estão preservadas no notebook versionado. Por isso, os resultados apresentados nesta Model Card foram recuperados dos metadados dos artefatos e das evidências documentadas no projeto.

---

## 14. Conclusão

Os modelos de inadimplência e recuperabilidade constituem protótipos experimentais desenvolvidos para demonstrar a aplicação de técnicas de Machine Learning à análise financeira municipal.

A ausência de resultados observados de pagamento e recuperação impede sua utilização como instrumentos de previsão real ou tomada de decisão administrativa.

Sua utilização futura depende da obtenção de dados adequados, validação estatística, avaliação de equidade, proteção de dados pessoais, revisão humana e aprovação jurídica.

A Model Card deve ser atualizada sempre que houver alterações relevantes nos dados, objetivos, variáveis, algoritmos ou condições de utilização dos modelos.
