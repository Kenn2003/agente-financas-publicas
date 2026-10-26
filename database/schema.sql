-- Schema do banco de dados do projeto Agente Finanças Públicas
-- Banco recomendado: PostgreSQL
-- Os dados originais estão em data/ready/.
-- Nenhuma coluna foi inventada em relação ao diagnóstico dos Parquets.

BEGIN;

CREATE TABLE IF NOT EXISTS carga_dados (
    carga_id BIGSERIAL PRIMARY KEY,
    nome_arquivo TEXT NOT NULL,
    tabela_destino TEXT NOT NULL,
    data_carga TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quantidade_registros BIGINT,
    observacoes TEXT,
    sucesso BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS arrecadacao (
    id TEXT PRIMARY KEY,
    receita_codigo TEXT NOT NULL,
    receita_descricao TEXT NOT NULL,
    receita_data_ocorrencia DATE NOT NULL,
    receita_valor NUMERIC(20, 2) NOT NULL,
    dia TEXT NOT NULL,
    mes TEXT NOT NULL,
    ano TEXT NOT NULL,
    valor_mes NUMERIC(20, 2) NOT NULL,
    valor_ano NUMERIC(20, 2) NOT NULL,
    valor_receita_ano NUMERIC(20, 2) NOT NULL,
    valor_receita_mes NUMERIC(20, 2) NOT NULL,
    valor_consolidado_mes NUMERIC(20, 2) NOT NULL,
    valor_consolidado_ano NUMERIC(20, 2) NOT NULL,
    codigo_conta_contabil TEXT NOT NULL,
    descricao_conta_contabil TEXT NOT NULL,
    data_atualizacao TIMESTAMP NOT NULL,
    valor_jan NUMERIC(20, 2) NOT NULL,
    valor_fev NUMERIC(20, 2) NOT NULL,
    valor_mar NUMERIC(20, 2) NOT NULL,
    valor_abr NUMERIC(20, 2) NOT NULL,
    valor_mai NUMERIC(20, 2) NOT NULL,
    valor_jun NUMERIC(20, 2) NOT NULL,
    valor_jul NUMERIC(20, 2) NOT NULL,
    valor_ago NUMERIC(20, 2) NOT NULL,
    valor_set NUMERIC(20, 2) NOT NULL,
    valor_out NUMERIC(20, 2) NOT NULL,
    valor_nov NUMERIC(20, 2) NOT NULL,
    valor_dez NUMERIC(20, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS folha_pagamento (
    id TEXT PRIMARY KEY,
    matricula TEXT NOT NULL,
    servidor TEXT NOT NULL,
    cod_setor TEXT,
    setor TEXT,
    cod_cargo TEXT,
    cargo TEXT,
    cod_funcao TEXT,
    cod_vinculo TEXT NOT NULL,
    vinculo TEXT NOT NULL,
    funcao TEXT,
    cod_secretaria TEXT,
    secretaria TEXT NOT NULL,
    data_admissao DATE NOT NULL,
    data_desligamento DATE,
    localizacao TEXT,
    vencimento_base NUMERIC(20, 2) NOT NULL,
    vencimento_outros NUMERIC(20, 2),
    vencimento_ferias NUMERIC(20, 2) NOT NULL,
    desconto_previpalmas NUMERIC(20, 2) NOT NULL,
    desconto_irrf NUMERIC(20, 2) NOT NULL,
    desconto_outros NUMERIC(20, 2),
    valor_rendimento NUMERIC(20, 2),
    valor_descontos NUMERIC(20, 2),
    valor_rendimento_liquido NUMERIC(20, 2) NOT NULL,
    ativo BOOLEAN NOT NULL,
    admitido_exonerado BOOLEAN NOT NULL,
    mes_referencia TEXT NOT NULL,
    ano_referencia TEXT NOT NULL,
    data_atualizacao TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS gastos_diretos (
    id TEXT PRIMARY KEY,
    processo TEXT NOT NULL,
    ficha TEXT NOT NULL,
    cod_unidade TEXT NOT NULL,
    unidade TEXT NOT NULL,
    cod_funcao TEXT NOT NULL,
    funcao TEXT NOT NULL,
    cod_sub_funcao TEXT NOT NULL,
    sub_funcao TEXT NOT NULL,
    cod_programa TEXT NOT NULL,
    programa TEXT NOT NULL,
    cod_proj_ativ TEXT NOT NULL,
    proj_ativ TEXT NOT NULL,
    cod_natureza TEXT NOT NULL,
    natureza TEXT NOT NULL,
    cod_subnatureza TEXT NOT NULL,
    subnatureza TEXT NOT NULL,
    fornecedor TEXT NOT NULL,
    cod_fonte TEXT NOT NULL,
    fonte TEXT NOT NULL,
    empenho TEXT NOT NULL,
    liquidacao TEXT NOT NULL,
    data_liquidacao DATE,
    cpf_cnpj TEXT NOT NULL,
    data DATE NOT NULL,
    data_pagamento DATE,
    numero_pagamento TEXT NOT NULL,
    valor_anulado NUMERIC(20, 2) NOT NULL,
    valor_anual_empenhado NUMERIC(20, 2) NOT NULL,
    valor_empenho NUMERIC(20, 2) NOT NULL,
    valor_pago NUMERIC(20, 2) NOT NULL,
    valor_liq NUMERIC(20, 2) NOT NULL,
    data_atualizacao TIMESTAMP NOT NULL,
    ano_referencia TEXT NOT NULL,
    mes_referencia TEXT NOT NULL,
    diaria BOOLEAN NOT NULL,
    historico TEXT,
    cotacao TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS receitas_recentes (
    ano TEXT NOT NULL,
    mes TEXT NOT NULL,
    codigo TEXT NOT NULL,
    orgao TEXT NOT NULL,
    codigo_original TEXT NOT NULL,
    total TEXT NOT NULL,
    orgao_nome TEXT NOT NULL,
    descricao TEXT NOT NULL,
    valor_orcado NUMERIC(20, 2) NOT NULL,
    valor_arrecado_mes NUMERIC(20, 2) NOT NULL,
    valor_arrecado_periodo NUMERIC(20, 2) NOT NULL,
    covid TEXT NOT NULL,

    CONSTRAINT pk_receitas_recentes
        PRIMARY KEY (ano, mes, codigo, orgao, codigo_original)
);

-- Índices para consultas frequentes

CREATE INDEX IF NOT EXISTS idx_arrecadacao_ano
    ON arrecadacao (ano);

CREATE INDEX IF NOT EXISTS idx_arrecadacao_codigo
    ON arrecadacao (receita_codigo);

CREATE INDEX IF NOT EXISTS idx_arrecadacao_data
    ON arrecadacao (receita_data_ocorrencia);

CREATE INDEX IF NOT EXISTS idx_folha_secretaria
    ON folha_pagamento (secretaria);

CREATE INDEX IF NOT EXISTS idx_folha_periodo
    ON folha_pagamento (ano_referencia, mes_referencia);

CREATE INDEX IF NOT EXISTS idx_folha_matricula
    ON folha_pagamento (matricula);

CREATE INDEX IF NOT EXISTS idx_gastos_processo
    ON gastos_diretos (processo);

CREATE INDEX IF NOT EXISTS idx_gastos_fornecedor
    ON gastos_diretos (fornecedor);

CREATE INDEX IF NOT EXISTS idx_gastos_periodo
    ON gastos_diretos (ano_referencia, mes_referencia);

CREATE INDEX IF NOT EXISTS idx_gastos_data_pagamento
    ON gastos_diretos (data_pagamento);

CREATE INDEX IF NOT EXISTS idx_receitas_periodo
    ON receitas_recentes (ano, mes);

CREATE INDEX IF NOT EXISTS idx_receitas_codigo
    ON receitas_recentes (codigo, codigo_original);

CREATE INDEX IF NOT EXISTS idx_receitas_orgao
    ON receitas_recentes (orgao);

COMMIT;