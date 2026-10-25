from contextlib import contextmanager
from pathlib import Path
import os

import psycopg2
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def obter_configuracao():
    """Obtém as configurações do PostgreSQL a partir do arquivo .env."""
    nomes = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    faltantes = [nome for nome in nomes if not os.getenv(nome)]

    if faltantes:
        raise RuntimeError(
            "Variáveis ausentes no .env: " + ", ".join(faltantes)
        )

    return {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


@contextmanager
def conectar():
    """Abre uma conexão e garante seu fechamento."""
    conexao = psycopg2.connect(**obter_configuracao())

    try:
        yield conexao
    finally:
        conexao.close()


def executar_consulta(consulta, parametros=None):
    """
    Executa uma consulta parametrizada e retorna os registros como dicionários.
    """
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(consulta, parametros or ())

            if cursor.description is None:
                conexao.commit()
                return []

            colunas = [descricao[0] for descricao in cursor.description]
            registros = cursor.fetchall()

            return [
                dict(zip(colunas, registro))
                for registro in registros
            ]


def contar_registros():
    """Retorna a quantidade de registros de cada tabela de dados."""
    consulta = """
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
    """

    return executar_consulta(consulta)


def listar_cargas():
    """Lista as cargas registradas na tabela de auditoria."""
    consulta = """
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
    """

    return executar_consulta(consulta)


def arrecadacao_por_ano(ano=None):
    """Consulta valores de arrecadação agrupados por ano."""
    consulta = """
        SELECT
            ano,
            SUM(receita_valor) AS total_arrecadado,
            COUNT(*) AS quantidade_registros
        FROM arrecadacao
        WHERE (%s IS NULL OR ano = %s)
        GROUP BY ano
        ORDER BY ano;
    """

    return executar_consulta(consulta, (ano, ano))


def gastos_por_ano(ano=None):
    """Consulta gastos agrupados por ano."""
    consulta = """
        SELECT
            ano_referencia,
            SUM(valor_pago) AS total_pago,
            SUM(valor_empenho) AS total_empenhado,
            COUNT(*) AS quantidade_registros
        FROM gastos_diretos
        WHERE (%s IS NULL OR ano_referencia = %s)
        GROUP BY ano_referencia
        ORDER BY ano_referencia;
    """

    return executar_consulta(consulta, (ano, ano))


def folha_por_secretaria():
    """Consulta a quantidade de registros e valores por secretaria."""
    consulta = """
        SELECT
            secretaria,
            COUNT(*) AS quantidade_registros,
            SUM(valor_rendimento_liquido) AS total_rendimento_liquido
        FROM folha_pagamento
        GROUP BY secretaria
        ORDER BY total_rendimento_liquido DESC NULLS LAST;
    """

    return executar_consulta(consulta)