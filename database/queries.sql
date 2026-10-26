-- Consultas compatíveis com o schema atual do projeto.
-- Tabelas utilizadas:
-- arrecadacao, folha_pagamento, gastos_diretos,
-- receitas_recentes e carga_dados.


-- 1. Quantidade de registros por tabela
SELECT 'arrecadacao' AS tabela, COUNT(*) AS registros
FROM arrecadacao
UNION ALL
SELECT 'folha_pagamento', COUNT(*)
FROM folha_pagamento
UNION ALL
SELECT 'gastos_diretos', COUNT(*)
FROM gastos_diretos
UNION ALL
SELECT 'receitas_recentes', COUNT(*)
FROM receitas_recentes
UNION ALL
SELECT 'carga_dados', COUNT(*)
FROM carga_dados
ORDER BY tabela;


-- 2. Histórico das cargas realizadas
SELECT
    carga_id,
    nome_arquivo,
    tabela_destino,
    data_carga,
    quantidade_registros,
    sucesso,
    observacoes
FROM carga_dados
ORDER BY data_carga DESC;


-- 3. Arrecadação total por ano
SELECT
    ano,
    SUM(receita_valor) AS total_arrecadado,
    COUNT(*) AS quantidade_registros
FROM arrecadacao
GROUP BY ano
ORDER BY ano;


-- 4. Arrecadação por código de receita
SELECT
    receita_codigo,
    receita_descricao,
    SUM(receita_valor) AS total_arrecadado,
    COUNT(*) AS quantidade_registros
FROM arrecadacao
GROUP BY receita_codigo, receita_descricao
ORDER BY total_arrecadado DESC;


-- 5. Gastos por ano de referência
SELECT
    ano_referencia,
    SUM(valor_anual_empenhado) AS total_empenhado,
    SUM(valor_liq) AS total_liquidado,
    SUM(valor_pago) AS total_pago,
    COUNT(*) AS quantidade_registros
FROM gastos_diretos
GROUP BY ano_referencia
ORDER BY ano_referencia;


-- 6. Gastos por unidade administrativa
SELECT
    cod_unidade,
    unidade,
    SUM(valor_pago) AS total_pago,
    COUNT(*) AS quantidade_registros
FROM gastos_diretos
GROUP BY cod_unidade, unidade
ORDER BY total_pago DESC;


-- 7. Folha por secretaria
SELECT
    secretaria,
    COUNT(*) AS quantidade_registros,
    SUM(valor_rendimento_liquido) AS total_rendimento_liquido
FROM folha_pagamento
GROUP BY secretaria
ORDER BY total_rendimento_liquido DESC NULLS LAST;


-- 8. Receitas recentes por período
SELECT
    ano,
    mes,
    SUM(valor_arrecado_mes) AS total_arrecadado_mes,
    SUM(valor_arrecado_periodo) AS total_arrecadado_periodo,
    COUNT(*) AS quantidade_registros
FROM receitas_recentes
GROUP BY ano, mes
ORDER BY ano, mes;


-- 9. Verificação de data sentinela em gastos
SELECT COUNT(*) AS datas_sentinela
FROM gastos_diretos
WHERE data_liquidacao <= DATE '1900-01-01';


-- 10. Verificação de duplicidades de ID
SELECT
    'arrecadacao' AS tabela,
    id,
    COUNT(*) AS quantidade
FROM arrecadacao
GROUP BY id
HAVING COUNT(*) > 1

UNION ALL

SELECT
    'folha_pagamento',
    id,
    COUNT(*)
FROM folha_pagamento
GROUP BY id
HAVING COUNT(*) > 1

UNION ALL

SELECT
    'gastos_diretos',
    id,
    COUNT(*)
FROM gastos_diretos
GROUP BY id
HAVING COUNT(*) > 1;