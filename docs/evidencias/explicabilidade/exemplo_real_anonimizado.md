# Evidência de explicabilidade — Sprint 5

## Natureza do exemplo

Foi utilizado um registro real da base de dívida ativa pertencente ao conjunto
temporal de teste da Sprint 4. Nenhum nome, CPF/CNPJ ou outro identificador
pessoal é utilizado ou registrado nesta evidência.

## Entradas efetivamente utilizadas

- `log_valor_divida`: 6.2088
- `idade_divida_dias`: 83

## Modelo de inadimplência proxy

- Algoritmo: `RandomForestClassifier`
- Classe prevista: `0`
- Probabilidade da classe 0: 0.6525
- Probabilidade da classe 1: 0.3475

### Feature Importance global

- `log_valor_divida`: 0.9013 (90.13%)
- `idade_divida_dias`: 0.0987 (9.87%)

## Modelo de recuperabilidade proxy

- Algoritmo: `RandomForestClassifier`
- Classe prevista: `media`

### Probabilidades

- Alta: 0.0062
- Baixa: 0.0068
- Média: 0.9870

### Feature Importance global

- `log_valor_divida`: 0.7375 (73.75%)
- `idade_divida_dias`: 0.2625 (26.25%)

## Limitação metodológica

Os dois modelos possuem `target_status = sintetico_proxy_nao_observado`.
A base disponível não contém rótulos observados de pagamento, inadimplência
ou recuperação. Portanto, as probabilidades acima descrevem o comportamento
dos modelos experimentais e não podem ser interpretadas como probabilidades
reais relativas ao contribuinte.

A técnica de Feature Importance é utilizada como explicação global. Ela indica
a relevância das variáveis para o modelo como um todo, não a contribuição
individual ou causal de cada variável para esta previsão específica.

## Governança

> Não usar para decisões reais: a base não contém rótulos observados de pagamento, inadimplência ou recuperação.

O exemplo é exclusivamente demonstrativo e não autoriza priorização,
restrição de direitos ou decisão de cobrança sem revisão humana.
