# Proteção ao IPTU Social — Sprint 05 (E3)

**Responsável:** Kenneth Wanderson Pereira Veras
**Projeto:** Sistema de Inteligência Tributária — Palmas/TO
**Referência:** 24/11/2026

## 1. Objetivo e escopo

Implementar uma camada determinística de governança para evitar que a ausência de informações cadastrais ou resultados experimentais sejam interpretados como autorização de cobrança individualizada. O protótipo é analítico, não executa cobrança tributária e não concede nem revoga benefícios.

## 2. Fundamentação normativa preliminar

A implementação adota como referência a LC Municipal 285/2013, art. 20, incisos II e III, §§ 1º e 2º. Os critérios abaixo descrevem as regras implementadas, não constituem parecer jurídico. A redação vigente, eventuais alterações e a aplicabilidade ao exercício devem ser verificadas antes de uso administrativo.

- Isenção pessoal: categoria de idade superior a 65 anos, aposentadoria, pensão ou deficiência física incapacitante para o trabalho, combinada com os requisitos implementados de imóvel edificado único, uso exclusivamente residencial, renda mensal de até dois salários mínimos e IPTU bruto inferior a 150 UFIP.
- Isenção automática: pessoa física, imóvel único com uma edificação, uso exclusivamente residencial, IPTU bruto inferior a 50 UFIP e exclusão de garagem ou box autônomo.

Referência legislativa: [LC 285/2013](https://legislativo.palmas.to.gov.br/media/leis/lei-complementar-285-2013-10-31-21-2-2024-17-23-49.pdf).

## 3. Arquitetura

| Componente | Responsabilidade |
|---|---|
| `src/governance/iptu_social.py` | Avaliação determinística, validação de entradas e elegibilidade em três estados |
| `src/governance/controle_cobranca.py` | Interface restrita de consulta e barreira para operações futuras |
| `src/governance/demo_iptu_social.py` | Demonstração com casos sintéticos |
| `src/agents/divida_ativa/` | Ferramentas analíticas e consulta à política de proteção |
| `src/agents/orchestrador.py` | Roteamento e inclusão de decisão estruturada quando dívida ativa é selecionada |

A ferramenta `verificar_protecao_iptu_social(exercicio)` não recebe atributos pessoais nem permite ao LLM declarar verificação oficial. O exercício de referência implementado é 2026; ano de inscrição em dívida ativa não equivale ao exercício de origem do tributo.

## 4. Política de decisão

| Condição | Decisão |
|---|---|
| Benefício oficialmente reconhecido | `bloquear` |
| Dados inválidos, ausentes, não verificados, benefício pendente/desconhecido ou possível elegibilidade | `revisao_humana` |
| Situação oficialmente verificada, benefício não reconhecido e ambas as modalidades avaliadas como não elegíveis | `prosseguir_demais_controles` |

O último estado não autoriza cobrança: apenas permite prosseguir para controles adicionais. A barreira `exigir_liberacao_governanca` rejeita exercícios fora do escopo e decisões diferentes de prosseguimento. Sua aplicação a operações reais futuras deverá ocorrer antes de qualquer efeito externo, com dados administrativos autenticados e vinculados ao contribuinte e ao exercício.

Na base atual, a consulta retorna `revisao_humana`, `cobranca_autorizada: false` e elegibilidade indeterminada. A política segue o princípio fail-closed diante de insuficiência de informação.

## 5. Validação automatizada

Execução consolidada reportada em 24/11/2026: 106 testes aprovados, zero falhas, um aviso de depreciação do plugin anyio, duração de 7,50 s.

| Suíte | Testes aprovados |
|---|---:|
| `tests/test_iptu_social.py` | 53 |
| `tests/test_integracao_iptu_social.py` | 45 |
| `tests/test_governanca_orquestrador.py` | 8 |
| Total | 106 |

| Módulo | Instruções | Ramificações | Cobertura |
|---|---:|---:|---:|
| `iptu_social.py` | 94 | 34 | 100% |
| `controle_cobranca.py` | 16 | 8 | 100% |
| Total | 110 | 42 | 100% |

Os testes abrangem limites de elegibilidade, dados inválidos e ausentes, situações administrativas, argumentos não autorizados, operações simuladas e integração do orquestrador mediante mocks. A cobertura refere-se exclusivamente aos dois módulos indicados.

### Reprodução

Na raiz do repositório, com dependências instaladas:

```bash
python -m pytest tests/test_iptu_social.py tests/test_integracao_iptu_social.py tests/test_governanca_orquestrador.py -v --cov=src.governance.iptu_social --cov=src.governance.controle_cobranca --cov-branch --cov-report=term-missing
```

Evidências previstas em `docs/evidencias/`: relatório textual, JUnit XML e cobertura XML/HTML.

## 6. Limitações e uso responsável

- A base analítica de dívida ativa não fornece os atributos administrativos necessários para verificar benefícios individuais, nem permite presumir que toda inscrição corresponda a IPTU.
- A decisão estruturada do orquestrador depende da seleção do agente de dívida ativa. Os testes com mocks não comprovam o roteamento real nem impedem toda recomendação textual indevida pelo LLM.
- A barreira foi testada em operações simuladas; não existe operação real de cobrança integrada nos componentes analisados. Um indicador booleano de verificação não substitui autenticação da fonte administrativa.
- Os modelos de classificação e recuperação usam alvos sintéticos. Suas métricas não comprovam capacidade preditiva real ou equidade individual.
- Indicadores territoriais não comprovam renda, idade, deficiência ou elegibilidade de pessoas. Não devem ser utilizados para priorizar cobrança.
- Cobertura integral de código não equivale a segurança integral, conformidade jurídica ou conformidade com a LGPD.
- A validação funcional com o provedor real e a revisão jurídica permanecem pendentes de evidência.

## 7. Conclusão

A E3 demonstra uma política determinística de proteção, integrada à interface analítica e ao fluxo simulado do orquestrador, com evidência automatizada reproduzível. O uso administrativo depende de validação jurídica, fontes oficiais, controles de acesso, rastreabilidade e revisão humana.
