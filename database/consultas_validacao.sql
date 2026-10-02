-- ============================================================
-- AGENTE FINANÇAS PÚBLICAS
-- Sprint 2 - Consultas SQL de validação
-- Responsável: Rafael Gonçalves
-- ============================================================

SET search_path TO financas;

-- ============================================================
-- 1. QUANTIDADE DE REGISTROS CARREGADOS
-- Verifica quantos registros da dívida ativa foram inseridos.
-- ============================================================

SELECT COUNT(*) AS total_registros
FROM divida_ativa;


-- ============================================================
-- 2. PERÍODO DOS DADOS
-- Verifica a data mais antiga e a data mais recente da amostra.
-- ============================================================

SELECT
    MIN("Data da Inscrição") AS data_mais_antiga,
    MAX("Data da Inscrição") AS data_mais_recente
FROM divida_ativa;


-- ============================================================
-- 3. VALIDAÇÃO DOS VALORES DA DÍVIDA
-- Exibe menor valor, maior valor, média e soma total das dívidas.
-- ============================================================

SELECT
    MIN("Valor Total da Dívida") AS menor_divida,
    MAX("Valor Total da Dívida") AS maior_divida,
    ROUND(AVG("Valor Total da Dívida"), 2) AS media_divida,
    SUM("Valor Total da Dívida") AS valor_total
FROM divida_ativa;


-- ============================================================
-- 4. VERIFICAÇÃO DE VALORES NULOS
-- Verifica se existem registros sem nome, valor ou data.
-- ============================================================

SELECT
    COUNT(*) FILTER (WHERE "Nome" IS NULL) AS nomes_nulos,
    COUNT(*) FILTER (WHERE "Valor Total da Dívida" IS NULL) AS valores_nulos,
    COUNT(*) FILTER (WHERE "Data da Inscrição" IS NULL) AS datas_nulas
FROM divida_ativa;


-- ============================================================
-- 5. VERIFICAÇÃO DE DUPLICIDADES
-- Considera duplicado um registro com mesmo nome, valor e data.
-- ============================================================

SELECT COUNT(*) AS grupos_duplicados
FROM (
    SELECT
        "Nome",
        "Valor Total da Dívida",
        "Data da Inscrição",
        COUNT(*) AS quantidade
    FROM divida_ativa
    GROUP BY
        "Nome",
        "Valor Total da Dívida",
        "Data da Inscrição"
    HAVING COUNT(*) > 1
) AS duplicados;


-- ============================================================
-- 6. AMOSTRA DOS DADOS CARREGADOS
-- Permite visualizar alguns registros para validação manual.
-- ============================================================

SELECT
    id,
    "Nome",
    "Valor Total da Dívida",
    "Data da Inscrição"
FROM divida_ativa
ORDER BY id
LIMIT 10;