import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

try:
    from .transform import transformar
    from .validation import validar
except ImportError:
    from transform import transformar
    from validation import validar


RAIZ = Path(__file__).resolve().parents[2]

ARQUIVOS = {
    "arrecadacao": "historico_arrecadacao.csv",
    "gastos_diretos": "historico_gastos_diretos.csv",
    "folha_pagamento": "historico_folha_pagamento.csv",
    "receitas_recentes": "atual_receitas.csv",
}


def executar(raiz=RAIZ, bases=None):
    raiz = Path(raiz)

    origem = raiz / "data" / "raw" / "csv"
    pronto = raiz / "data" / "processed"
    logs = raiz / "logs"

    pronto.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)

    nome_log = datetime.now(timezone.utc).strftime(
        "etl_%Y%m%dT%H%M%SZ.log"
    )

    logger = logging.getLogger("etl_sefin")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.FileHandler(
        logs / nome_log,
        encoding="utf-8"
    )

    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s"
        )
    )

    logger.addHandler(handler)

    relatorio = {
        "executado_em": datetime.now(timezone.utc).isoformat(),
        "bases": {},
        "pendencias": [
            "enriquecimento IBGE (Matheus)",
            "carga relacional (Karyne)"
        ]
    }

    try:
        for nome in (bases if bases is not None else list(ARQUIVOS)):

            if nome not in ARQUIVOS:
                raise ValueError(
                    f"Base não cadastrada: {nome}"
                )

            arquivo = origem / ARQUIVOS[nome]

            if not arquivo.is_file():
                logger.warning(
                    "%s: arquivo ausente %s",
                    nome,
                    arquivo
                )

                relatorio["bases"][nome] = {
                    "status": "ausente",
                    "arquivo": str(arquivo)
                }
                continue

            logger.info("Iniciando %s", nome)

            try:
                df = pd.read_csv(
                    arquivo,
                    sep=",",
                    encoding="utf-8-sig",
                    dtype=str,
                    low_memory=False
                )

                tratado, transformacoes = transformar(
                    df, nome
                )

                qualidade = validar(
                    tratado, nome
                )

                destino = pronto / f"{nome}.csv"
                temporario = pronto / f"{nome}.tmp.csv"

                tratado.to_csv(
                    temporario,
                    index=False,
                    sep=",",
                    encoding="utf-8-sig"
                )

                temporario.replace(destino)

                relatorio["bases"][nome] = {
                    "status": "ok",
                    "origem": str(arquivo),
                    "destino": str(destino),
                    "transformacoes": transformacoes,
                    "qualidade": qualidade
                }

                logger.info(
                    "%s: %s linhas processadas",
                    nome,
                    len(tratado)
                )

                del df, tratado

            except Exception as erro:
                relatorio["bases"][nome] = {
                    "status": "erro",
                    "mensagem": str(erro)
                }

                logger.exception(
                    "%s: erro no processamento",
                    nome
                )

        caminho = logs / "qualidade_ultima_execucao.json"

        caminho.write_text(
            json.dumps(
                relatorio,
                indent=2,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        return relatorio

    finally:
        handler.close()
        logger.removeHandler(handler)


def main():
    parser = argparse.ArgumentParser(
        description="ETL dos CSVs municipais"
    )

    parser.add_argument(
        "--raiz",
        type=Path,
        default=RAIZ
    )

    parser.add_argument(
        "--base",
        action="append",
        choices=list(ARQUIVOS),
        help="Omitir para processar todas as bases"
    )

    args = parser.parse_args()

    resultado = executar(
        args.raiz,
        args.base
    )

    print(
        json.dumps(
            {
                k: v["status"]
                for k, v in resultado["bases"].items()
            },
            ensure_ascii=False,
            indent=2
        )
    )

    if any(
        v["status"] != "ok"
        for v in resultado["bases"].values()
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
