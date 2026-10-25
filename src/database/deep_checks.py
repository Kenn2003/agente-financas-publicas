from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
READY_DIR = ROOT / "data" / "ready"
DOCS_DIR = ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "deep_checks.txt"


def write_line(lines, text=""):
    lines.append(str(text))


def check_key(df, columns, name, lines):
    missing = [column for column in columns if column not in df.columns]

    if missing:
        write_line(lines, f"{name}: colunas ausentes: {missing}")
        return

    duplicated = int(df.duplicated(subset=columns, keep=False).sum())
    groups = int(df.duplicated(subset=columns, keep=False).sum())

    write_line(lines, f"{name}")
    write_line(lines, f"  Colunas: {columns}")
    write_line(lines, f"  Registros pertencentes a grupos repetidos: {groups}")

    if duplicated > 0:
        repeated = (
            df.loc[df.duplicated(subset=columns, keep=False), columns]
            .value_counts()
            .head(10)
        )

        write_line(lines, "  Exemplos:")
        for key, count in repeated.items():
            write_line(lines, f"    - {key}: {count} ocorrências")


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    lines = []

    lines.append("VERIFICAÇÕES APROFUNDADAS")
    lines.append("Nenhum arquivo Parquet foi alterado.")
    lines.append("")

    # Folha de pagamento
    folha_path = READY_DIR / "folha_pagamento.parquet"
    folha = pd.read_parquet(folha_path)

    lines.append("=" * 80)
    lines.append("FOLHA DE PAGAMENTO")
    lines.append("=" * 80)

    write_line(lines, f"Registros: {len(folha)}")
    write_line(lines, f"IDs distintos: {folha['id'].nunique(dropna=False)}")

    check_key(
        folha,
        ["matricula", "ano_referencia", "mes_referencia"],
        "Chave candidata: matricula + ano_referencia + mes_referencia",
        lines,
    )

    check_key(
        folha,
        ["id", "ano_referencia", "mes_referencia"],
        "Chave candidata: id + ano_referencia + mes_referencia",
        lines,
    )

    # IDs repetidos com períodos
    if "id" in folha.columns:
        repeated_ids = folha[folha["id"].duplicated(keep=False)].copy()

        if not repeated_ids.empty:
            period_counts = (
                repeated_ids.groupby("id")
                .agg(
                    ocorrencias=("id", "size"),
                    periodos=("ano_referencia", "nunique"),
                    meses=("mes_referencia", "nunique"),
                )
                .sort_values("ocorrencias", ascending=False)
                .head(20)
            )

            lines.append("")
            lines.append("IDs repetidos e quantidade de períodos:")
            lines.append(period_counts.to_string())

    # Datas sentinela
    lines.append("")
    lines.append("Datas sentinela na folha:")

    for column in ["data_admissao", "data_desligamento", "data_atualizacao"]:
        if column in folha.columns:
            count = int(
                (folha[column] == pd.Timestamp("0001-01-01")).sum()
            )
            lines.append(f"  - {column}: {count}")

    # Gastos diretos
    gastos_path = READY_DIR / "gastos_diretos.parquet"
    gastos = pd.read_parquet(gastos_path)

    lines.append("")
    lines.append("=" * 80)
    lines.append("GASTOS DIRETOS")
    lines.append("=" * 80)

    if "data_liquidacao" in gastos.columns:
        sentinel_count = int(
            (gastos["data_liquidacao"] == pd.Timestamp("0001-01-01")).sum()
        )
        lines.append(
            f"data_liquidacao igual a 0001-01-01: {sentinel_count}"
        )

    check_key(
        gastos,
        ["processo", "empenho", "liquidacao"],
        "Chave candidata: processo + empenho + liquidacao",
        lines,
    )

    # Receitas recentes
    receitas_path = READY_DIR / "receitas_recentes.parquet"
    receitas = pd.read_parquet(receitas_path)

    lines.append("")
    lines.append("=" * 80)
    lines.append("RECEITAS RECENTES")
    lines.append("=" * 80)

    check_key(
        receitas,
        ["ano", "mes", "codigo", "orgao"],
        "Chave candidata: ano + mes + codigo + orgao",
        lines,
    )

    check_key(
        receitas,
        ["ano", "mes", "codigo", "orgao", "descricao"],
        "Chave candidata: ano + mes + codigo + orgao + descricao",
        lines,
    )

    OUTPUT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"Relatório criado em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()