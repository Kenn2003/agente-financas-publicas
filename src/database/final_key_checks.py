from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
READY_DIR = ROOT / "data" / "ready"
DOCS_DIR = ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "final_key_checks.txt"


def check_uniqueness(df, columns, name, lines):
    missing = [column for column in columns if column not in df.columns]

    if missing:
        lines.append(f"{name}")
        lines.append(f"Colunas ausentes: {missing}")
        lines.append("")
        return

    total = len(df)
    distinct = df[columns].drop_duplicates().shape[0]
    repeated_rows = int(df.duplicated(subset=columns, keep=False).sum())

    lines.append(name)
    lines.append(f"Colunas: {columns}")
    lines.append(f"Registros: {total}")
    lines.append(f"Combinações distintas: {distinct}")
    lines.append(f"Registros em combinações repetidas: {repeated_rows}")
    lines.append(
        f"É única: {'SIM' if repeated_rows == 0 else 'NÃO'}"
    )
    lines.append("")


def main():
    lines = [
        "VERIFICAÇÃO FINAL DE CHAVES",
        "Nenhum arquivo Parquet foi alterado.",
        "",
    ]

    # Folha de pagamento
    folha = pd.read_parquet(
        READY_DIR / "folha_pagamento.parquet"
    )

    folha_deduplicada = folha.drop_duplicates()

    lines.append("=" * 80)
    lines.append("FOLHA DE PAGAMENTO")
    lines.append("=" * 80)
    lines.append(f"Registros originais: {len(folha)}")
    lines.append(
        f"Registros após remoção de cópias exatas: "
        f"{len(folha_deduplicada)}"
    )
    lines.append(
        f"Linhas removidas: {len(folha) - len(folha_deduplicada)}"
    )
    lines.append("")

    check_uniqueness(
        folha_deduplicada,
        ["id"],
        "Unicidade do id após deduplicação",
        lines,
    )

    check_uniqueness(
        folha_deduplicada,
        ["matricula", "ano_referencia", "mes_referencia"],
        "Unicidade de matrícula e período",
        lines,
    )

    # Gastos diretos
    gastos = pd.read_parquet(
        READY_DIR / "gastos_diretos.parquet"
    )

    lines.append("=" * 80)
    lines.append("GASTOS DIRETOS")
    lines.append("=" * 80)

    check_uniqueness(
        gastos,
        ["id"],
        "Unicidade do id de gastos",
        lines,
    )

    check_uniqueness(
        gastos,
        ["processo", "empenho", "liquidacao"],
        "Unicidade da chave operacional de gastos",
        lines,
    )

    # Receitas recentes
    receitas = pd.read_parquet(
        READY_DIR / "receitas_recentes.parquet"
    )

    lines.append("=" * 80)
    lines.append("RECEITAS RECENTES")
    lines.append("=" * 80)

    check_uniqueness(
        receitas,
        ["ano", "mes", "codigo", "orgao", "codigo_original"],
        "Chave ampliada com codigo_original",
        lines,
    )

    check_uniqueness(
        receitas,
        [
            "ano",
            "mes",
            "codigo",
            "orgao",
            "codigo_original",
            "descricao",
        ],
        "Chave ampliada com codigo_original e descricao",
        lines,
    )

    OUTPUT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"Relatório criado em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()