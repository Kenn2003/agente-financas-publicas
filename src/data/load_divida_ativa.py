import os
from pathlib import Path

import pandas as pd
import psycopg


# Caminho da raiz do projeto
BASE_DIR = Path(__file__).resolve().parents[2]

# Arquivo utilizado como amostra de dados
CSV_PATH = BASE_DIR / "relatorio_dívida_ativa.csv"


def carregar_e_tratar_csv():
    """Lê, trata e valida os dados de dívida ativa."""

    df = pd.read_csv(
        CSV_PATH,
        sep=";",
        encoding="utf-8-sig"
    )

    print(f"Registros encontrados no CSV: {len(df)}")

    # Converte valores no padrão brasileiro:
    # Ex.: 3.264,31 -> 3264.31
    df["Valor Total da Dívida"] = pd.to_numeric(
        df["Valor Total da Dívida"]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    # Converte DD/MM/AAAA para data
    df["Data da Inscrição"] = pd.to_datetime(
        df["Data da Inscrição"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    valores_invalidos = df["Valor Total da Dívida"].isna().sum()
    datas_invalidas = df["Data da Inscrição"].isna().sum()
    duplicados = df.duplicated().sum()

    print(f"Valores inválidos: {valores_invalidos}")
    print(f"Datas inválidas: {datas_invalidas}")
    print(f"Registros duplicados: {duplicados}")

    # Remove registros inválidos
    df = df.dropna(
        subset=[
            "Nome",
            "Valor Total da Dívida",
            "Data da Inscrição"
        ]
    )

    # Remove duplicidades exatas
    df = df.drop_duplicates()

    print(f"Registros após tratamento: {len(df)}")

    return df


def conectar_banco():
    """Cria uma conexão segura com o PostgreSQL/Supabase."""

    senha = os.environ.get("DB_PASSWORD")

    if not senha:
        raise RuntimeError(
            "A variável de ambiente DB_PASSWORD não foi definida."
        )

    return psycopg.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        port=5432,
        dbname="postgres",
        user="postgres.fjvmerlwygryndtyqvbu",
        password=senha
    )


def inserir_dados(df):
    """Insere a amostra tratada na tabela financas.divida_ativa."""

    registros = [
        (
            linha["Nome"],
            float(linha["Valor Total da Dívida"]),
            linha["Data da Inscrição"].date()
        )
        for _, linha in df.iterrows()
    ]

    with conectar_banco() as conn:
        with conn.cursor() as cursor:

            # Garante que uma nova execução não duplique a amostra.
            cursor.execute("TRUNCATE TABLE financas.divida_ativa RESTART IDENTITY;")

            cursor.executemany(
                """
                INSERT INTO financas.divida_ativa
                    ("Nome", "Valor Total da Dívida", "Data da Inscrição")
                VALUES (%s, %s, %s);
                """,
                registros
            )

        conn.commit()

    print(f"{len(registros)} registros inseridos com sucesso.")


def main():
    print("Iniciando carga da dívida ativa...")

    df = carregar_e_tratar_csv()
    inserir_dados(df)

    print("Carga concluída com sucesso.")


if __name__ == "__main__":
    main()