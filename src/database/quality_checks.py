from pathlib import Path

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype


ROOT = Path(__file__).resolve().parents[2]
READY_DIR = ROOT / "data" / "ready"
DOCS_DIR = ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "quality_checks.txt"

FILES = {
    "arrecadacao": READY_DIR / "arrecadacao.parquet",
    "folha_pagamento": READY_DIR / "folha_pagamento.parquet",
    "gastos_diretos": READY_DIR / "gastos_diretos.parquet",
    "receitas_recentes": READY_DIR / "receitas_recentes.parquet",
}

TEXT_COLUMNS = {
    "arrecadacao": [
        "receita_descricao",
        "descricao_conta_contabil",
    ],
    "folha_pagamento": [
        "servidor",
        "setor",
        "cargo",
        "secretaria",
        "funcao",
    ],
    "gastos_diretos": [
        "unidade",
        "funcao",
        "programa",
        "proj_ativ",
        "natureza",
        "subnatureza",
        "fornecedor",
        "historico",
    ],
    "receitas_recentes": [
        "orgao_nome",
        "descricao",
    ],
}

SENSITIVE_COLUMNS = {
    "folha_pagamento": [
        "servidor",
        "matricula",
        "data_admissao",
        "data_desligamento",
        "localizacao",
    ],
    "gastos_diretos": [
        "cpf_cnpj",
        "fornecedor",
    ],
}


def format_value(value):
    if pd.isna(value):
        return "NA"
    return str(value)


def inspect_file(name, path):
    lines = []

    lines.append("=" * 80)
    lines.append(f"DATASET: {name}")
    lines.append(f"ARQUIVO: {path}")
    lines.append("=" * 80)

    if not path.exists():
        lines.append("STATUS: arquivo não encontrado")
        return lines

    df = pd.read_parquet(path)

    lines.append(f"Registros: {len(df)}")
    lines.append(f"Colunas: {len(df.columns)}")
    lines.append("")

    # Duplicidades completas
    duplicated_rows = int(df.duplicated().sum())
    lines.append(f"Duplicidades completas: {duplicated_rows}")

    # Duplicidade por id
    if "id" in df.columns:
        id_nulls = int(df["id"].isna().sum())
        duplicated_ids = int(df["id"].duplicated(keep=False).sum())
        distinct_ids = int(df["id"].nunique(dropna=False))

        lines.append(f"IDs distintos: {distinct_ids}")
        lines.append(f"IDs nulos: {id_nulls}")
        lines.append(f"Registros com ID repetido: {duplicated_ids}")

        if duplicated_ids > 0:
            repeated = (
                df.loc[df["id"].duplicated(keep=False), "id"]
                .value_counts()
                .head(10)
            )
            lines.append("Exemplos de IDs repetidos:")
            for item, count in repeated.items():
                lines.append(f"  - {item}: {count} ocorrências")

    # Valores nulos
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0].sort_values(ascending=False)

    lines.append("")
    lines.append("Colunas com valores nulos:")
    if nulls.empty:
        lines.append("  Nenhuma")
    else:
        for column, count in nulls.items():
            percentage = (count / len(df)) * 100
            lines.append(
                f"  - {column}: {count} ({percentage:.2f}%)"
            )

    # Valores negativos
    numeric_columns = df.select_dtypes(
        include=["number"]
    ).columns

    lines.append("")
    lines.append("Colunas numéricas com valores negativos:")

    negative_found = False

    for column in numeric_columns:
        negative_count = int((df[column] < 0).sum())

        if negative_count > 0:
            negative_found = True
            minimum = df[column].min()
            lines.append(
                f"  - {column}: {negative_count} registros; "
                f"mínimo={minimum}"
            )

    if not negative_found:
        lines.append("  Nenhuma")

    # Datas
    date_columns = [
    column
    for column in df.columns
    if is_datetime64_any_dtype(df[column])
    ]

    lines.append("")
    lines.append("Intervalos das colunas de data:")

    if len(date_columns) == 0:
        lines.append("  Nenhuma coluna datetime identificada")
    else:
        for column in date_columns:
            minimum = df[column].min()
            maximum = df[column].max()
            lines.append(
                f"  - {column}: {minimum} até {maximum}"
            )

    # Colunas sensíveis
    sensitive = [
        column
        for column in SENSITIVE_COLUMNS.get(name, [])
        if column in df.columns
    ]

    lines.append("")
    lines.append("Colunas que exigem cuidado de privacidade:")
    if sensitive:
        for column in sensitive:
            lines.append(f"  - {column}")
    else:
        lines.append("  Nenhuma identificada neste dataset")

    # Codificação textual: amostras com caracteres suspeitos
    text_columns = [
        column
        for column in TEXT_COLUMNS.get(name, [])
        if column in df.columns
    ]

    suspicious_chars = ("╟", "╙", "╩", "├", "═", "╒", "┴", "τ", "π")

    lines.append("")
    lines.append("Possíveis caracteres corrompidos:")

    suspicious_found = False

    for column in text_columns:
        values = df[column].dropna().astype(str)
        matches = values[
            values.apply(
                lambda value: any(char in value for char in suspicious_chars)
            )
        ]

        if not matches.empty:
            suspicious_found = True
            lines.append(
                f"  - {column}: {len(matches)} possíveis ocorrências"
            )
            for example in matches.head(3):
                lines.append(f"      exemplo: {example}")

    if not suspicious_found:
        lines.append("  Nenhum padrão suspeito encontrado")

    # Tipos
    lines.append("")
    lines.append("Tipos das colunas:")
    for column, dtype in df.dtypes.items():
        lines.append(f"  - {column}: {dtype}")

    lines.append("")
    return lines


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    report = []
    report.append("RELATÓRIO DE VERIFICAÇÃO DE QUALIDADE DOS DADOS")
    report.append("Este relatório é apenas diagnóstico.")
    report.append("Nenhum arquivo Parquet foi alterado.")
    report.append("")

    for name, path in FILES.items():
        try:
            report.extend(inspect_file(name, path))
        except Exception as error:
            report.append("=" * 80)
            report.append(f"DATASET: {name}")
            report.append(f"ERRO DURANTE A LEITURA: {error}")
            report.append("=" * 80)

    OUTPUT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    print(f"Relatório criado em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()