-- ============================================================
-- AGENTE FINANÇAS PÚBLICAS
-- Modelo relacional para integração dos CSVs
-- PostgreSQL / Supabase
-- ============================================================

CREATE SCHEMA IF NOT EXISTS financas;
SET search_path TO financas;


-- ============================================================
-- 1. ÓRGÃOS
-- ============================================================

CREATE TABLE IF NOT EXISTS orgaos (
    id BIGSERIAL PRIMARY KEY,
    codigo_origem TEXT,
    nome TEXT NOT NULL,
    CONSTRAINT uq_orgao UNIQUE (codigo_origem, nome)
);


-- ============================================================
-- 2. FORNECEDORES / CREDORES
-- ============================================================

CREATE TABLE IF NOT EXISTS fornecedores (
    id BIGSERIAL PRIMARY KEY,
    cpf_cnpj TEXT,
    nome TEXT NOT NULL,
    CONSTRAINT uq_fornecedor UNIQUE (cpf_cnpj, nome)
);


-- ============================================================
-- 3. LICITAÇÕES
-- Cabeçalhos iguais aos do CSV
-- ============================================================

CREATE TABLE IF NOT EXISTS licitacoes (
    id BIGSERIAL PRIMARY KEY,

    "Número" TEXT,
    "Órgão" TEXT,
    "Número do Processo" TEXT,
    "Modalidade" TEXT,
    "Ano" INTEGER,

    "Data de Publicação" DATE,
    "Data de Homologação" DATE,
    "Data de Protocolo" DATE,
    "Data de Abertura" DATE,

    "Valor" NUMERIC(18,2),

    "Fundamento" TEXT,
    "Situação" TEXT,
    "Descrição" TEXT,
    "Contratos" TEXT,
    "Empenhos" TEXT,
    "Vencedores" TEXT,
    "Itens em Aberto" TEXT
);


-- ============================================================
-- 4. CONTRATOS
-- ============================================================

CREATE TABLE IF NOT EXISTS contratos (
    id BIGSERIAL PRIMARY KEY,

    chave_contrato TEXT UNIQUE,

    orgao_id BIGINT REFERENCES orgaos(id),
    licitacao_id BIGINT REFERENCES licitacoes(id),

    numero TEXT,
    ano INTEGER,

    objeto TEXT,
    valor NUMERIC(18,2),

    data_firmatura DATE,
    inicio_vigencia DATE,
    fim_vigencia DATE,
    data_publicacao DATE,

    tipo TEXT,
    tipo_adt TEXT,

    fiscal_contrato TEXT,
    situacao TEXT,
    covid TEXT
);


-- ============================================================
-- 5. CONTRATO x FORNECEDOR
-- Relação N:N
-- ============================================================

CREATE TABLE IF NOT EXISTS contrato_fornecedor (
    contrato_id BIGINT NOT NULL
        REFERENCES contratos(id)
        ON DELETE CASCADE,

    fornecedor_id BIGINT NOT NULL
        REFERENCES fornecedores(id),

    PRIMARY KEY (contrato_id, fornecedor_id)
);


-- ============================================================
-- 6. DESPESAS / EMPENHOS
-- ============================================================

CREATE TABLE IF NOT EXISTS despesas (
    id BIGSERIAL PRIMARY KEY,

    chave_empenho TEXT UNIQUE,

    orgao_id BIGINT REFERENCES orgaos(id),
    fornecedor_id BIGINT REFERENCES fornecedores(id),
    licitacao_id BIGINT REFERENCES licitacoes(id),

    tipo TEXT,

    empenho TEXT,
    ficha TEXT,

    ano INTEGER,
    numero TEXT,
    data DATE,

    valor_empenho NUMERIC(18,2),
    valor_mov NUMERIC(18,2),
    valor_liquidacao NUMERIC(18,2),
    valor_pagamento NUMERIC(18,2),
    valor NUMERIC(18,2),

    descricao TEXT,
    movimento TEXT,

    pagamento TEXT,
    acumulado_pagamento NUMERIC(18,2),
    liquidado NUMERIC(18,2),

    desativado BOOLEAN
);


-- ============================================================
-- 7. PAGAMENTOS DE PALMAS
-- ============================================================

CREATE TABLE IF NOT EXISTS pagamentos (
    id BIGSERIAL PRIMARY KEY,

    despesa_id BIGINT REFERENCES despesas(id),
    fornecedor_id BIGINT REFERENCES fornecedores(id),

    processo TEXT,
    ficha TEXT,

    cod_unidade TEXT,
    unidade TEXT,

    cod_funcao TEXT,
    funcao TEXT,

    cod_sub_funcao TEXT,
    sub_funcao TEXT,

    cod_programa TEXT,
    programa TEXT,

    cod_proj_ativ TEXT,
    proj_ativ TEXT,

    cod_natureza TEXT,
    natureza TEXT,

    cod_subnatureza TEXT,
    subnatureza TEXT,

    gestao TEXT,

    cod_fonte TEXT,
    fonte TEXT,

    empenho TEXT,
    liquidacao TEXT,

    data_liquidacao DATE,
    data DATE,
    data_vencimento DATE,
    data_pagamento DATE,

    numero_pagamento TEXT,

    valor_orcamento NUMERIC(18,2),
    valor_orcamento_cred_esp NUMERIC(18,2),
    valor_suplementado NUMERIC(18,2),
    valor_reduzido NUMERIC(18,2),

    valor_empenhado NUMERIC(18,2),
    valor_anulado NUMERIC(18,2),
    valor_reserva NUMERIC(18,2),
    valor_saldo NUMERIC(18,2),

    valor_anual_empenhado NUMERIC(18,2),
    valor_empenho NUMERIC(18,2),
    valor_pago NUMERIC(18,2),
    valor_liq NUMERIC(18,2),
    valor_a_pagar NUMERIC(18,2),

    ano_referencia INTEGER,
    mes_referencia INTEGER,

    diaria TEXT,
    historico TEXT,
    cotacao TEXT
);


-- ============================================================
-- 8. SERVIDORES
-- ============================================================

CREATE TABLE IF NOT EXISTS servidores (
    id BIGSERIAL PRIMARY KEY,

    chave_origem TEXT UNIQUE,
    orgao_id BIGINT REFERENCES orgaos(id),

    cpf_mascarado TEXT,
    matricula TEXT,
    nome TEXT,

    cargo TEXT,
    funcao TEXT,

    lotacao TEXT,
    local_trabalho TEXT,
    vinculo TEXT,

    data_admissao DATE,
    data_desligamento DATE,

    carga_horaria NUMERIC(10,2),
    carga_horaria_semanal NUMERIC(10,2),

    tipo TEXT,

    ano INTEGER,
    mes INTEGER,

    salario_base NUMERIC(18,2),
    proventos NUMERIC(18,2),
    descontos NUMERIC(18,2),
    liquido NUMERIC(18,2),

    situacao_servidor TEXT
);


-- ============================================================
-- 9. FOLHA DE PAGAMENTO
-- ============================================================

CREATE TABLE IF NOT EXISTS folha_pagamento (
    id BIGSERIAL PRIMARY KEY,

    servidor_id BIGINT REFERENCES servidores(id),

    matricula TEXT,
    cpf TEXT,
    servidor TEXT,

    cod_setor TEXT,
    setor TEXT,

    cod_cargo TEXT,
    cargo TEXT,

    cod_funcao TEXT,
    funcao TEXT,

    cod_vinculo TEXT,
    vinculo TEXT,

    cod_secretaria TEXT,
    secretaria TEXT,

    data_admissao DATE,
    data_desligamento DATE,

    localizacao TEXT,

    vencimento_base NUMERIC(18,2),
    vencimento_outros NUMERIC(18,2),
    vencimento_ferias NUMERIC(18,2),

    desconto_previpalmas NUMERIC(18,2),
    desconto_irrf NUMERIC(18,2),
    desconto_outros NUMERIC(18,2),

    valor_rendimento NUMERIC(18,2),
    valor_descontos NUMERIC(18,2),
    valor_rendimento_liquido NUMERIC(18,2),

    ativo BOOLEAN,
    admitido_exonerado TEXT,

    mes_referencia INTEGER,
    ano_referencia INTEGER,

    data_atualizacao TIMESTAMP
);


-- ============================================================
-- 10. RECEITAS
-- Fonte: receita_acessoinformacao
-- ============================================================

CREATE TABLE IF NOT EXISTS receitas (
    id BIGSERIAL PRIMARY KEY,

    orgao_id BIGINT REFERENCES orgaos(id),

    orgao_nome TEXT,
    unidade_nome TEXT,
    unidade_id TEXT,

    codigo TEXT,
    codigo_original TEXT,

    ano INTEGER,
    mes INTEGER,

    descricao TEXT,

    valor_orcado NUMERIC(18,2),
    valor_arrecadado_mes NUMERIC(18,2),
    valor_arrecadado_periodo NUMERIC(18,2),

    covid TEXT
);


-- ============================================================
-- 11. RECEITAS PALMAS
-- ============================================================

CREATE TABLE IF NOT EXISTS receitas_palmas (
    id BIGSERIAL PRIMARY KEY,

    receita_codigo TEXT,
    receita_descricao TEXT,

    receita_data_ocorrencia DATE,
    receita_valor NUMERIC(18,2),

    dia INTEGER,
    mes INTEGER,
    ano INTEGER,

    valor_mes NUMERIC(18,2),
    valor_ano NUMERIC(18,2),

    valor_receita_ano NUMERIC(18,2),
    valor_receita_mes NUMERIC(18,2),

    valor_consolidado_mes NUMERIC(18,2),
    valor_consolidado_ano NUMERIC(18,2),

    codigo_conta_contabil TEXT,
    descricao_conta_contabil TEXT,

    data_atualizacao TIMESTAMP
);


-- ============================================================
-- 12. DÍVIDA ATIVA
-- Cabeçalhos iguais aos do CSV
-- ============================================================

CREATE TABLE IF NOT EXISTS divida_ativa (
    id BIGSERIAL PRIMARY KEY,

    "Nome" TEXT,
    "Valor Total da Dívida" NUMERIC(18,2),
    "Data da Inscrição" DATE
);


-- ============================================================
-- 13. SANÇÕES ADMINISTRATIVAS
-- Cabeçalhos iguais aos do CSV
-- ============================================================

CREATE TABLE IF NOT EXISTS sancoes_administrativas (
    id BIGSERIAL PRIMARY KEY,

    "Sanção" TEXT,
    "Nome" TEXT,
    "CPF/CNPJ" TEXT,
    "Início" DATE,
    "Término" DATE
);


-- ============================================================
-- ÍNDICES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_licitacoes_orgao
ON licitacoes("Órgão");

CREATE INDEX IF NOT EXISTS idx_contratos_orgao
ON contratos(orgao_id);

CREATE INDEX IF NOT EXISTS idx_contratos_licitacao
ON contratos(licitacao_id);

CREATE INDEX IF NOT EXISTS idx_despesas_orgao
ON despesas(orgao_id);

CREATE INDEX IF NOT EXISTS idx_despesas_fornecedor
ON despesas(fornecedor_id);

CREATE INDEX IF NOT EXISTS idx_despesas_licitacao
ON despesas(licitacao_id);

CREATE INDEX IF NOT EXISTS idx_pagamentos_despesa
ON pagamentos(despesa_id);

CREATE INDEX IF NOT EXISTS idx_pagamentos_fornecedor
ON pagamentos(fornecedor_id);

CREATE INDEX IF NOT EXISTS idx_servidores_orgao
ON servidores(orgao_id);

CREATE INDEX IF NOT EXISTS idx_folha_servidor
ON folha_pagamento(servidor_id);

CREATE INDEX IF NOT EXISTS idx_receitas_orgao
ON receitas(orgao_id);