from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
READY_DIR = ROOT / "data" / "ready"
DOCS_DIR = ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "conflict_checks.txt"


def analyze_repeated_key(df, key_columns, dataset_name, lines):
    lines.append("=" * 80)
    lines.append(f"{dataset_name}")
    lines.append(f"Chave analisada: {key_columns}")
    lines.append("=" * 80)

    repeated_mask = df.duplicated(subset=key_columns, keep=False)
    repeated = df.loc[repeated_mask].copy()

    if repeated.empty:
        lines.append("Nenhum grupo repetido encontrado.")
        lines.append("")
        return

    grouped = repeated.groupby(key_columns, dropna=False, sort=False)

    total_groups = 0
    exact_groups = 0
    conflicting_groups = 0

    examples = []

    for key, group in grouped:
        total_groups += 1

        # Remove as colunas da chave para verificar se os demais campos são iguais
        non_key_columns = [
            column for column in df.columns
            if column not in key_columns
        ]

        different_values = group[non_key_columns].nunique(
            dropna=False
        )

        has_conflict = bool((different_values > 1).any())

        if has_conflict:
            conflicting_groups += 1

            varying_columns = list(
                different_values[different_values > 1].index
            )

            if len(examples) < 5:
                examples.append(
                    (
                        key,
                        len(group),
                        varying_columns,
                    )
                )
        else:
            exact_groups += 1

    lines.append(f"Registros em grupos repetidos: {len(repeated)}")
    lines.append(f"Quantidade de grupos repetidos: {total_groups}")
    lines.append(f"Grupos com registros totalmente iguais: {exact_groups}")
    lines.append(f"Grupos com diferenças: {conflicting_groups}")
    lines.append("")

    if examples:
        lines.append("Exemplos de grupos com diferenças:")
        for key, count, varying_columns in examples:
            lines.append(f"- Chave: {key}")
            lines.append(f"  Registros no grupo: {count}")
            lines.append(
                f"  Colunas diferentes: {varying_columns}"
            )
    else:
        lines.append(
            "Não foram encontrados exemplos de grupos com diferenças."
        )

    lines.append("")


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    lines = []

    lines.append("ANÁLISE DE CONFLITOS EM CHAVES REPETIDAS")
    lines.append("Nenhum arquivo Parquet foi alterado.")
    lines.append("")

    folha = pd.read_parquet(
        READY_DIR / "folha_pagamento.parquet"
    )

    analyze_repeated_key(
        folha,
        ["id", "ano_referencia", "mes_referencia"],
        "FOLHA — id e período",
        lines,
    )

    analyze_repeated_key(
        folha,
        ["matricula", "ano_referencia", "mes_referencia"],
        "FOLHA — matrícula e período",
        lines,
    )

    gastos = pd.read_parquet(
        READY_DIR / "gastos_diretos.parquet"
    )

    analyze_repeated_key(
        gastos,
        ["processo", "empenho", "liquidacao"],
        "GASTOS — processo, empenho e liquidação",
        lines,
    )

    receitas = pd.read_parquet(
        READY_DIR / "receitas_recentes.parquet"
    )

    analyze_repeated_key(
        receitas,
        ["ano", "mes", "codigo", "orgao"],
        "RECEITAS — ano, mês, código e órgão",
        lines,
    )

    analyze_repeated_key(
        receitas,
        ["ano", "mes", "codigo", "orgao", "descricao"],
        "RECEITAS — chave ampliada",
        lines,
    )

    OUTPUT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"Relatório criado em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()