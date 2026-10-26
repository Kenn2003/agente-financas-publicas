from pathlib import Path
from datetime import date, datetime

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "ready"

TABELAS = {
    "arrecadacao": [
        "id", "receita_codigo", "receita_descricao",
        "receita_data_ocorrencia", "receita_valor", "dia", "mes", "ano",
        "valor_mes", "valor_ano", "valor_receita_ano",
        "valor_receita_mes", "valor_consolidado_mes",
        "valor_consolidado_ano", "codigo_conta_contabil",
        "descricao_conta_contabil", "data_atualizacao", "valor_jan",
        "valor_fev", "valor_mar", "valor_abr", "valor_mai",
        "valor_jun", "valor_jul", "valor_ago", "valor_set",
        "valor_out", "valor_nov", "valor_dez",
    ],
    "folha_pagamento": [
        "id", "matricula", "servidor", "cod_setor", "setor",
        "cod_cargo", "cargo", "cod_funcao", "cod_vinculo", "vinculo",
        "funcao", "cod_secretaria", "secretaria", "data_admissao",
        "data_desligamento", "localizacao", "vencimento_base",
        "vencimento_outros", "vencimento_ferias",
        "desconto_previpalmas", "desconto_irrf", "desconto_outros",
        "valor_rendimento", "valor_descontos",
        "valor_rendimento_liquido", "ativo", "admitido_exonerado",
        "mes_referencia", "ano_referencia", "data_atualizacao",
    ],
    "gastos_diretos": [
        "id", "processo", "ficha", "cod_unidade", "unidade",
        "cod_funcao", "funcao", "cod_sub_funcao", "sub_funcao",
        "cod_programa", "programa", "cod_proj_ativ", "proj_ativ",
        "cod_natureza", "natureza", "cod_subnatureza", "subnatureza",
        "fornecedor", "cod_fonte", "fonte", "empenho", "liquidacao",
        "data_liquidacao", "cpf_cnpj", "data", "data_pagamento",
        "numero_pagamento", "valor_anulado", "valor_anual_empenhado",
        "valor_empenho", "valor_pago", "valor_liq",
        "data_atualizacao", "ano_referencia", "mes_referencia",
        "diaria", "historico", "cotacao",
    ],
    "receitas_recentes": [
        "ano", "mes", "codigo", "orgao", "codigo_original", "total",
        "orgao_nome", "descricao", "valor_orcado",
        "valor_arrecado_mes", "valor_arrecado_periodo", "covid",
    ],
}


def carregar_configuracao():
    load_dotenv(ROOT / ".env")

    obrigatorias = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    faltantes = [nome for nome in obrigatorias if not os.getenv(nome)]

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


def preparar_dataframe(nome, dataframe):
    dataframe = dataframe.copy()

    colunas_esperadas = TABELAS[nome]
    colunas_obtidas = list(dataframe.columns)

    if set(colunas_obtidas) != set(colunas_esperadas):
        raise ValueError(
            f"Colunas inesperadas em {nome}.\n"
            f"Esperadas: {colunas_esperadas}\n"
            f"Obtidas: {colunas_obtidas}"
        )
    dataframe = dataframe[colunas_esperadas]

    if nome == "folha_pagamento":
        antes = len(dataframe)
        dataframe = dataframe.drop_duplicates(keep="first")
        depois = len(dataframe)
        print(f"folha_pagamento: {antes - depois} duplicatas completas removidas")

    colunas_date = {
        "arrecadacao": ["receita_data_ocorrencia"],
        "folha_pagamento": ["data_admissao", "data_desligamento"],
        "gastos_diretos": ["data_liquidacao", "data", "data_pagamento"],
        "receitas_recentes": [],
    }

    colunas_timestamp = {
        "arrecadacao": ["data_atualizacao"],
        "folha_pagamento": ["data_atualizacao"],
        "gastos_diretos": ["data_atualizacao"],
        "receitas_recentes": [],
    }

    for coluna in colunas_date[nome]:
        dataframe[coluna] = pd.to_datetime(
            dataframe[coluna],
            errors="coerce"
        ).dt.date

    for coluna in colunas_timestamp[nome]:
        dataframe[coluna] = pd.to_datetime(
            dataframe[coluna],
            errors="coerce"
        )

    if nome == "gastos_diretos":
        coluna = "data_liquidacao"
        dataframe.loc[
            dataframe[coluna].apply(
                lambda valor: (
                pd.notna(valor)
                and isinstance(valor, date)
                and valor <= date(1900, 1, 1)
            )
        ),
        coluna,
    ] = None

    return dataframe


def converter_valor(valor):
    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(valor, pd.Timestamp):
        return valor.to_pydatetime()

    if hasattr(valor, "item"):
        try:
            return valor.item()
        except ValueError:
            pass

    return valor


def carregar_tabela(cursor, nome, dataframe):
    colunas = TABELAS[nome]
    registros = [
        tuple(converter_valor(valor) for valor in linha)
        for linha in dataframe[colunas].itertuples(
            index=False,
            name=None
        )
    ]

    tabela_sql = sql.Identifier(nome)
    colunas_sql = sql.SQL(", ").join(
        sql.Identifier(coluna) for coluna in colunas
    )

    comando = sql.SQL(
        "INSERT INTO {} ({}) VALUES %s"
    ).format(tabela_sql, colunas_sql)

    tamanho_lote = 5000

    for inicio in range(0, len(registros), tamanho_lote):
        lote = registros[inicio:inicio + tamanho_lote]
        execute_values(
            cursor,
            comando.as_string(cursor.connection),
            lote,
            page_size=tamanho_lote,
        )

    cursor.execute(
        """
        INSERT INTO carga_dados
            (nome_arquivo, tabela_destino, quantidade_registros, observacoes)
        VALUES (%s, %s, %s, %s);
        """,
        (
            f"{nome}.parquet",
            nome,
            len(registros),
            "Carga inicial a partir de data/ready; "
            "deduplicação integral aplicada somente à folha.",
        ),
    )

    return len(registros)


def verificar_banco_vazio(cursor):
    for nome in TABELAS:
        cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(nome)
            )
        )
        quantidade = cursor.fetchone()[0]

        if quantidade != 0:
            raise RuntimeError(
                f"A tabela {nome} já possui {quantidade} registros. "
                "A carga foi interrompida para evitar duplicação."
            )


def main():
    configuracao = carregar_configuracao()

    conexao = psycopg2.connect(**configuracao)

    try:
        with conexao:
            with conexao.cursor() as cursor:
                verificar_banco_vazio(cursor)

                total_geral = 0

                for nome in TABELAS:
                    caminho = DATA_DIR / f"{nome}.parquet"

                    if not caminho.is_file():
                        raise FileNotFoundError(
                            f"Arquivo não encontrado: {caminho}"
                        )

                    print(f"Lendo {caminho}...")
                    dataframe = pd.read_parquet(caminho)

                    dataframe = preparar_dataframe(
                        nome,
                        dataframe
                    )

                    quantidade = carregar_tabela(
                        cursor,
                        nome,
                        dataframe
                    )

                    total_geral += quantidade
                    print(
                        f"{nome}: {quantidade} registros inseridos"
                    )

                print(f"Total inserido: {total_geral}")

    finally:
        conexao.close()


if __name__ == "__main__":
    main()