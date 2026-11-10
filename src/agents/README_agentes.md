# Agentes de Finanças Públicas — Arquitetura, Dados e Proteção de Dados

> **Local no repositório:** `src/agents/README.md`  
> **Projeto:** `agente-financas-publicas` — análise de finanças públicas municipais de Palmas (TO)  
> **Estado:** documentação da implementação atual e do planejamento de novos agentes.  
> **Atenção:** os controles de privacidade descritos como *previstos* ainda precisam ser implementados e testados. Este documento não constitui certificação de conformidade à LGPD.

## 1. Objetivo e escopo

O projeto organiza consultas sobre dados públicos municipais por meio de agentes especializados, coordenados por um orquestrador. A arquitetura separa interpretação de perguntas, execução de consultas locais, consolidação de resultados e apresentação de respostas. A implementação deve privilegiar resultados rastreáveis, informar limites de cobertura e impedir que o modelo de linguagem receba dados pessoais desnecessários.

**Agentes atuais:** Receitas e Despesas.  
**Agentes planejados:** Folha de Pagamento e Dívida Ativa.  
**Integração planejada:** interface de consulta e inclusão progressiva dos especialistas no orquestrador.

## 2. Estrutura de arquivos

```text
src/agents/
├── README.md
├── orchestrador.py
├── prompts_orchestrador.py
├── receitas/
│   ├── agent.py
│   ├── tools.py
│   ├── prompts.py
│   └── validation.py
├── despesas/
│   ├── agent.py
│   ├── tools.py
│   └── prompts.py
├── folha/                  # planejado
│   ├── agent.py
│   ├── tools.py
│   ├── prompts.py
│   └── validation.py
└── divida_ativa/           # planejado
    ├── agent.py
    ├── tools.py
    ├── prompts.py
    └── validation.py
```

A árvore é ilustrativa: confirme os arquivos existentes antes de usá-la como inventário do repositório. O nome do módulo `orchestrador.py` segue a implementação informada; mantenha os imports compatíveis com o nome efetivamente adotado no código.

## 3. Orquestrador

**Módulos:** `orchestrador.py` e `prompts_orchestrador.py`.

O orquestrador é o ponto de entrada para consultas em linguagem natural. Sua responsabilidade é identificar o domínio da pergunta, selecionar os agentes disponíveis, encaminhar tarefas especializadas e apresentar as respostas com suas fontes e ressalvas. Não deve inventar números nem calcular resultados fiscais a partir de séries incompatíveis.

### Fluxo

1. Receber e validar a pergunta.
2. Classificar a intenção entre os domínios habilitados.
3. Dividir perguntas multidomínio em tarefas independentes (por exemplo, arrecadação para Receitas e execução orçamentária para Despesas).
4. Acionar somente os agentes necessários.
5. Distinguir sucesso, falha parcial, erro e consulta fora do escopo.
6. Combinar as respostas **sem apagar ressalvas**, divergências ou limitações de cobertura.

**Situação atual:** roteamento e execução conjunta de Receitas e Despesas testados. Permanecem pontos de aprimoramento: isolamento de contexto entre especialistas, tratamento estruturado de erros do provedor, controle de quota e consistência da síntese. Um `status: ok` significa que as chamadas retornaram, **não** que todos os números foram conciliados ou que as respostas estão livres de contradição.

**Regra de segurança:** o orquestrador deve transmitir aos agentes apenas parâmetros necessários à consulta. Nunca deve encaminhar tabelas brutas contendo dados pessoais para um modelo externo.

## 4. Agente de Receitas — implementado

**Local:** `src/agents/receitas/`  
**Fonte atual:** `data/processed/receitas_recentes.csv`.

### Responsabilidades

- Consultar arrecadação por ano e, quando disponível, mês ou órgão.
- Analisar evolução e comparar períodos compatíveis.
- Localizar órgãos na base e esclarecer filtros utilizados.

### Ferramentas disponíveis

| Ferramenta | Finalidade |
|---|---|
| `consultar_receitas(ano, mes=None, orgao=None, codigo_orgao=None)` | Total de arrecadação filtrado |
| `evolucao_arrecadacao(ano, orgao=None)` | Evolução dentro do ano |
| `comparar_periodos(ano_inicial, ano_final, orgao=None)` | Comparação entre anos |
| `buscar_orgaos(termo, ano=None)` | Busca de órgãos |

### Regras de interpretação

- Evitar dupla contagem decorrente da estrutura hierárquica dos códigos de receita; a implementação atual utiliza categorias de primeiro nível.
- Não tratar `valor_arrecado_periodo` automaticamente como acumulado sem verificar sua semântica.
- Distinguir ausência de dados de arrecadação igual a zero.
- Indicar ano, meses efetivamente cobertos, filtros, arquivo de origem e eventuais lacunas.
- **Não afirmar conciliação oficial:** os resultados ainda requerem confronto com demonstrativos contábeis/fiscais.

## 5. Agente de Despesas — implementado, resultados preliminares

**Local:** `src/agents/despesas/`  
**Fonte histórica:** `data/processed/gastos_diretos.csv`  
**Consolidador:** `src/data/consolidar_despesas.py`.

### Responsabilidades

- Consultar empenhos, liquidações e pagamentos.
- Rastrear registros associados a um empenho.
- Sinalizar inconsistências e limitações de conciliação.

### Ferramentas disponíveis

| Ferramenta | Finalidade |
|---|---|
| `consultar_execucao(ano, codigo_unidade=None)` | Totais preliminares por exercício/unidade |
| `consultar_execucao_empenho(ano, codigo_unidade, numero_empenho)` | Execução de empenho específico |
| `rastrear_empenho(ano, codigo_unidade, numero_empenho)` | Rastreabilidade de registros |

### Cuidados de modelagem

- A fonte histórica possui aproximadamente **344.323 registros**, com dados de 2001 até parte de 2021; não presumir cobertura anual completa para 2021.
- `ano_referencia` corresponde ao exercício de referência do empenho; **não equivale necessariamente ao ano de desembolso**.
- Chaves compostas de empenho, liquidação e pagamento são candidatas à identificação documental e requerem validação.
- Valores negativos, anulações e registros repetidos não devem ser eliminados automaticamente.
- Somas preliminares de linhas não representam, sem conciliação, saldos a liquidar, saldos a pagar, restos a pagar ou resultado fiscal.
- Divergência entre valores deve ser apresentada como **alerta de qualidade**, nunca como prova de irregularidade.

**Integração futura:** incorporar despesas recentes fornecidas pela equipe, com rastreamento de origem, controle de sobreposição entre fontes e validação de períodos.

## 6. Agente de Folha de Pagamento — planejado

**Fonte inicial:** `data/processed/folha_pagamento.csv`.

### Diagnóstico exploratório inicial

| Indicador | Resultado |
|---|---:|
| Registros | 489.378 |
| Colunas | 30 |
| 2016 | 124.639 registros; 12 meses |
| 2017 | 132.414 registros; 12 meses |
| 2018 | 133.651 registros; 12 meses |
| 2019 | 98.674 registros; 9 meses |
| IDs repetidos | 5.018 |
| Combinações `matricula` + ano + mês repetidas | 5.018 |
| Divergências nas três identidades financeiras testadas | 0 |

As três identidades verificadas foram: soma das parcelas de vencimento versus `valor_rendimento`; soma dos descontos versus `valor_descontos`; e rendimento menos descontos versus `valor_rendimento_liquido`. Os testes usaram tolerância de R$ 0,02 e preenchimento de alguns valores ausentes com zero para o cálculo. **Esses testes não validam a completude da folha, a autenticidade dos lançamentos nem a ausência de duplicidades econômicas.**

A base contém `matricula`, `servidor`, informações funcionais, valores remuneratórios, competências e datas de vínculo. Também contém vínculos como `PENSAO ALIMENTICIA`, `PENSIONISTA`, `APOSENTADO`, `ESTAGIARIO` e `BOLSISTA`; por isso, **linha de folha não é sinônimo de servidor ativo**.

### Antes da implementação

1. Verificar se os 5.018 IDs repetidos são linhas idênticas, versões de atualização ou eventos distintos; não deduplicar sem evidência.
2. Confirmar se existem pagamentos suplementares, múltiplos vínculos ou outras ocorrências por matrícula/competência.
3. Validar a cobertura dos meses de 2019 e os critérios de comparação anual.
4. Verificar a semântica de `ativo` e `admitido_exonerado` em cada competência.
5. Estabelecer quais categorias de vínculo entram em cada indicador.
6. Comparar o dicionário de dados com a nova base de servidores a ser fornecida pela equipe; **não presumir equivalência** entre cadastro funcional e lançamentos de folha.

### Funcionalidades previstas

- `consultar_folha(ano, mes=None, secretaria=None, vinculo=None)`: valores agregados, respeitando limites de divulgação.
- `evolucao_folha(ano, ...)`: evolução mensal somente para competências existentes.
- `distribuicao_vinculos(ano, ...)`: distribuição agregada de registros ou vínculos, com definição explícita da unidade de contagem.

**Proibido no MVP:** busca nominal, consulta por matrícula, listagem de remuneração individual ou geração de rankings de pessoas.

## 7. Agente de Dívida Ativa — planejado

O agente será incorporado após a inspeção do esquema, da procedência e das permissões de uso da base. A existência de informação em portal público **não implica autorização irrestrita para sua redistribuição ou envio a terceiros**.

### Riscos específicos

- Identificação de contribuintes pessoas físicas e de empresários individuais.
- Dados tributários, inscrições, débitos, endereços e eventuais identificadores pessoais.
- Risco de revelar situação fiscal individual, inclusive por combinações de filtros.
- Possível incidência de sigilo fiscal e de restrições legais específicas, além da LGPD.

### Escopo inicial sugerido

- Estoque agregado da dívida por exercício, natureza e situação, quando esses campos existirem.
- Evolução de inscrições, baixas e recebimentos, observando diferenças entre estoque e fluxo.
- Indicadores de recuperação com denominadores e cobertura claramente definidos.
- Supressão de resultados que permitam inferir a situação de um contribuinte específico.

**Não implementar** busca por CPF/CNPJ, nome, endereço, número de inscrição individual ou exposição de devedores sem análise jurídica, finalidade legítima, autorização adequada e controles específicos. Dados relativos a pessoas jurídicas também exigem cautela quando permitirem identificar pessoas naturais ou estiverem sujeitos a sigilo fiscal.

## 8. LGPD, sigilo e privacidade desde a concepção

A Lei nº 13.709/2018 (LGPD) estabelece princípios e requisitos para o tratamento de dados pessoais. O projeto também deverá observar normas de transparência pública, sigilo fiscal, segurança da informação e regras institucionais aplicáveis. **Publicidade de certos dados não dispensa análise de finalidade, necessidade e segurança.**

### 8.1 Princípios operacionais

- **Finalidade e adequação:** consultas vinculadas à análise de finanças públicas; impedir usos incompatíveis.
- **Necessidade/minimização:** acessar e retornar somente campos indispensáveis.
- **Transparência e qualidade:** documentar fonte, cobertura, transformação, versão e limitações.
- **Segurança e prevenção:** controlar acesso, armazenamento, logs, integrações e exposição de resultados.
- **Não discriminação:** não produzir perfis individuais ou inferências sobre pessoas a partir de remuneração, vínculos ou dívidas.
- **Responsabilização:** manter registro das decisões de modelagem e evidências de testes dos controles.

A base legal apropriada para cada tratamento deve ser definida pela instituição responsável, considerando a finalidade, a origem dos dados e a legislação aplicável. **Não presumir consentimento nem afirmar que o projeto é integralmente anônimo.**

### 8.2 Fluxo seguro proposto

```text
Pergunta do usuário
        ↓
Validação de intenção, escopo e parâmetros
        ↓
Orquestrador seleciona agente especializado
        ↓
Ferramenta consulta dados localmente (Pandas/SQL)
        ↓
Agregação + verificação de cobertura + controles de divulgação
        ↓
Resposta estruturada SEM identificadores pessoais
        ↓
Modelo de linguagem recebe apenas o resultado autorizado
        ↓
Resposta final com fonte, período, ressalvas e limitações
```

**Importante:** o uso de uma API externa de IA exige avaliação contratual, técnica e institucional do fluxo de dados. Os dados pessoais não devem constar de prompts, mensagens de erro ou logs enviados ao provedor. Também é necessário avaliar retenção, acesso, transferência internacional e eventuais operadores envolvidos.

### 8.3 Controles obrigatórios antes da liberação dos novos agentes

| Controle | Regra de implementação | Situação |
|---|---|---|
| Minimização | Selecionar somente colunas necessárias à agregação | Previsto |
| Bloqueio de identificadores | Não retornar `servidor`, `matricula`, CPF/CNPJ, endereço ou identificadores equivalentes | Previsto |
| Execução local | Consultar registros individuais apenas na camada de dados autorizada | Previsto |
| Agregação mínima | Definir limiar de tamanho de grupo por risco; não tratar um número fixo como garantia universal | Previsto |
| Supressão complementar | Impedir inferência de células pequenas por totais, diferenças ou filtros sucessivos | Previsto |
| Controle de consultas | Limitar granularidade, combinações de filtros e consultas repetidas | Previsto |
| Logs seguros | Registrar métricas e erros sem dados pessoais ou segredos | Previsto |
| Segredos | Chaves de API apenas em variáveis de ambiente/gestor de segredos; nunca no Git | Prática exigida; auditar |
| Testes de privacidade | Testar prompts adversariais, reidentificação e vazamentos | Previsto |
| Governança | Definir responsável, base legal, retenção e procedimento de incidentes | A definir institucionalmente |

**Atenção:** um limiar mínimo de grupo isolado não impede ataques por diferenciação. Filtros combinados, totais marginais e consultas sucessivas podem revelar valores individuais; por isso, são necessários controles complementares e testes adversariais.

### 8.4 Pseudonimização e anonimização

- **Pseudonimização:** substitui identificadores diretos por códigos ou hashes, mas ainda pode permitir vinculação e reidentificação; os dados continuam sujeitos à LGPD quando se referem a pessoas identificáveis.
- **Anonimização:** depende de avaliação contextual e de meios técnicos razoáveis de reversão/reidentificação; retirar nomes ou publicar agregados não é prova automática de anonimização.
- **Dados agregados:** preferidos para os agentes de Folha e Dívida Ativa, desde que avaliados quanto a grupos pequenos e inferência indireta.

### 8.5 Testes mínimos de privacidade

Antes de habilitar um novo agente no orquestrador, verificar que ele:

1. Recusa consultas por nome, matrícula, CPF/CNPJ ou outro identificador individual quando fora do escopo autorizado.
2. Não revela valores individuais por filtros de grupos muito pequenos.
3. Não permite reconstrução por diferença entre totais ou consultas encadeadas.
4. Não inclui registros brutos nos argumentos enviados ao modelo.
5. Não imprime dados pessoais em exceções, logs ou relatórios de teste.
6. Informa quando o resultado foi suprimido por privacidade, sem expor o valor protegido.
7. Não transforma ausência de dados em zero nem completa lacunas com valores inventados.

Utilizar dados sintéticos nos testes automatizados sempre que possível. Evitar colocar amostras reais de folha ou dívida ativa no repositório, em issues e em Pull Requests.

## 9. Qualidade, rastreabilidade e comparabilidade

Toda ferramenta deverá retornar, quando pertinente:

- `status`: sucesso, sem dados, inconsistência, erro ou supressão por privacidade;
- `fonte`: arquivo/tabela e, quando disponível, versão/data de atualização;
- `periodo`: competências efetivamente cobertas;
- `filtros`: parâmetros aplicados, sem identificadores pessoais;
- `indicadores`: valores agregados com unidade e definição;
- `ressalvas`: duplicidades, lacunas, inconsistências e limitações de comparação.

**Não comparar diretamente** arrecadação anual com despesas de período incompleto, nem usar ano de referência do empenho como se fosse ano de pagamento. **Não somar registros de folha sem investigar duplicidades**. A consolidação de dívida ativa deverá distinguir estoque, inscrição, recebimento, cancelamento e atualização monetária, conforme os campos efetivamente disponíveis.

## 10. Integração de novos agentes

Checklist para incorporar Folha, Dívida Ativa ou outro domínio:

- [ ] Mapear fonte, licença/condições de acesso, dicionário e cobertura.
- [ ] Identificar dados pessoais, dados protegidos por sigilo e riscos de inferência.
- [ ] Definir finalidade, base legal e permissões de acesso com os responsáveis.
- [ ] Implementar validação de parâmetros, agregação local e controles de divulgação.
- [ ] Testar integridade, granularidade, duplicidades e compatibilidade temporal.
- [ ] Testar privacidade, segurança e resistência a consultas adversariais.
- [ ] Criar prompt que proíba inferências, exposição de registros e invenção de valores.
- [ ] Registrar o agente no roteamento e testar consultas simples e multidomínio.
- [ ] Atualizar este README com ferramentas, fontes, limitações e estado real da implementação.

## 11. Prioridades imediatas

1. Corrigir o isolamento das perguntas especializadas no orquestrador e preservar erros parciais.
2. Confirmar cobertura e conciliação das bases atuais antes de comparações fiscais.
3. Investigar os **5.018 registros repetidos** na folha histórica e documentar a unidade de observação.
4. Implementar Folha de Pagamento inicialmente com **consultas agregadas e controles de privacidade**.
5. Avaliar a nova base de servidores da equipe e a futura base de Dívida Ativa antes de definir ferramentas definitivas.
6. Integrar os especialistas à interface com validação de entradas e respostas.

---

**Nota de manutenção:** este README é documentação técnica evolutiva. Cada funcionalidade descrita como planejada só deverá ser anunciada como implementada após revisão do código, testes e validação dos controles de proteção de dados.
