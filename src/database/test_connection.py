import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()


def main():
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "agente_financas_publicas"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user;")
            database, user = cursor.fetchone()

            print(f"Banco conectado: {database}")
            print(f"Usuário conectado: {user}")

            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
                """
            )

            print("Tabelas encontradas:")
            for (table_name,) in cursor.fetchall():
                print(f"- {table_name}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()