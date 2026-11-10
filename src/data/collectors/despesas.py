"""
Coletor de despesas do Portal da Transparência de Palmas.

Fonte atual:
    https://acessoainformacao.palmas.to.gov.br

Endpoint:
    sgdespesas/listar

Cobertura confirmada da fonte atual:
    janeiro/2022 em diante.

Observação sobre 2021:
    A API histórica integracao.palmas.to.gov.br possui um snapshot que
    alcança 01/06/2021. O Portal atual não retornou registros para meses
    posteriores de 2021 testados. Por isso este coletor não inventa nem
    preenche dados ausentes desse intervalo.

Tipos de movimento confirmados no JavaScript oficial:
    0 = Empenho
    1 = Liquidação
    2 = Pagamento
    3 = Anulação de Empenho
    4 = Anulação de Liquidação
    5 = Anulação de Pagamento
    6 = Retenção de Pagamento
"""

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


RAIZ = Path(__file__).resolve().parents[3]

BASE = "https://acessoainformacao.palmas.to.gov.br"
PAGINA = BASE + "/cidadao/transparencia/sgdespesas"
API = BASE + "/api"

ACAO = "sgdespesas/listar"

ANO_INICIAL = 2022
TAMANHO_PAGINA = 1000
TENTATIVAS = 5

PASTA_RAW = (
    RAIZ
    / "data"
    / "raw"
    / "atualizacoes"
    / "despesas"
)

ARQUIVO_CSV = (
    RAIZ
    / "data"
    / "raw"
    / "csv"
    / "atual_despesas.csv"
)

COLUNAS = [
    "chave_empenho",
    "tipo",
    "empenho",
    "ficha",
    "orgao_empenho",
    "orgao",
    "ano",
    "numero",
    "data",
    "cpf_cnpj",
    "fornecedor",
    "valor_empenho",
    "valor_mov",
    "descricao",
    "licitacao",
    "licitacao_label",
    "desativado",
    "total",
    "valor_liquidacao",
    "valor_pagamento",
    "movimento",
    "valor",
    "liquidado",
    "pagamento",
    "acumulado_liquidado",
    "acumulado_pagamento",
]


def criar_sessao():
    sessao = requests.Session()

    sessao.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": BASE,
            "Referer": PAGINA,
        }
    )

    resposta = sessao.get(
        PAGINA,
        timeout=30,
    )
    resposta.raise_for_status()

    return sessao


def executar_requisicao(
    sessao,
    ano,
    mes,
    offset,
    quantidade,
):
    parametros = {
        "k1": {
            "order": {},
            "limit": f"{offset}, {quantidade}",
            "acao": ACAO,
            "ano": str(ano),
            "mes": f"{mes:02d}",
        }
    }

    ultimo_erro = None

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = sessao.post(
                API,
                data={
                    "multi_request": "true",
                    "params": json.dumps(
                        parametros,
                        ensure_ascii=False,
                    ),
                },
                timeout=60,
            )

            if resposta.status_code == 403:
                sessao.get(
                    PAGINA,
                    timeout=30,
                ).raise_for_status()

                resposta = sessao.post(
                    API,
                    data={
                        "multi_request": "true",
                        "params": json.dumps(
                            parametros,
                            ensure_ascii=False,
                        ),
                    },
                    timeout=60,
                )

            resposta.raise_for_status()

            corpo = resposta.json()

            if "k1" not in corpo:
                raise RuntimeError(
                    "Resposta da API sem a chave 'k1'."
                )

            bloco = corpo["k1"]

            if not isinstance(bloco, dict):
                raise RuntimeError(
                    "Formato inesperado retornado pela API."
                )

            return bloco

        except (
            requests.RequestException,
            ValueError,
            RuntimeError,
        ) as erro:
            ultimo_erro = erro

            if tentativa == TENTATIVAS:
                break

            espera = tentativa * 2

            print(
                f"  tentativa {tentativa}/{TENTATIVAS} "
                f"falhou: {erro}"
            )
            print(
                f"  nova tentativa em {espera}s..."
            )

            time.sleep(espera)

    raise RuntimeError(
        f"Falha após {TENTATIVAS} tentativas: "
        f"{ultimo_erro}"
    )


def converter_total(valor):
    try:
        return int(valor or 0)
    except (TypeError, ValueError):
        return 0


def pasta_mes(ano, mes):
    return (
        PASTA_RAW
        / str(ano)
        / f"{mes:02d}"
    )


def limpar_paginas_mes(ano, mes):
    pasta = pasta_mes(ano, mes)
    pasta.mkdir(
        parents=True,
        exist_ok=True,
    )

    for arquivo in pasta.glob(
        "pagina_*.json"
    ):
        arquivo.unlink()


def salvar_pagina(
    ano,
    mes,
    numero_pagina,
    offset,
    quantidade,
    total,
    registros,
):
    pasta = pasta_mes(ano, mes)

    pasta.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivo = (
        pasta
        / f"pagina_{numero_pagina:06d}.json"
    )

    conteudo = {
        "fonte": PAGINA,
        "acao": ACAO,
        "ano": ano,
        "mes": mes,
        "offset": offset,
        "quantidade": quantidade,
        "total": total,
        "coletado_em": datetime.now(
            timezone.utc
        ).isoformat(),
        "registros": registros,
    }

    arquivo.write_text(
        json.dumps(
            conteudo,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def salvar_controle(
    ano,
    mes,
    total,
    paginas,
    teste=False,
):
    pasta = pasta_mes(ano, mes)

    controle = {
        "fonte": PAGINA,
        "acao": ACAO,
        "ano": ano,
        "mes": mes,
        "total_informado_api": total,
        "paginas_salvas": paginas,
        "teste": teste,
        "coletado_em": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    (
        pasta
        / "controle.json"
    ).write_text(
        json.dumps(
            controle,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def baixar_mes(
    sessao,
    ano,
    mes,
    teste=False,
):
    print(
        f"\nDespesas {ano}/{mes:02d}"
    )

    limpar_paginas_mes(
        ano,
        mes,
    )

    quantidade = (
        5
        if teste
        else TAMANHO_PAGINA
    )

    offset = 0
    numero_pagina = 1
    total = None
    total_baixado = 0

    while True:
        bloco = executar_requisicao(
            sessao,
            ano,
            mes,
            offset,
            quantidade,
        )

        registros = bloco.get(
            "dados",
            [],
        )

        if not isinstance(registros, list):
            raise RuntimeError(
                "Campo 'dados' não é uma lista."
            )

        total_resposta = converter_total(
            bloco.get("total")
        )

        if total is None:
            total = total_resposta

            print(
                f"  total informado pela API: "
                f"{total}"
            )

        salvar_pagina(
            ano=ano,
            mes=mes,
            numero_pagina=numero_pagina,
            offset=offset,
            quantidade=quantidade,
            total=total_resposta,
            registros=registros,
        )

        total_baixado += len(
            registros
        )

        print(
            f"  página {numero_pagina}: "
            f"{len(registros)} registros "
            f"(acumulado {total_baixado})"
        )

        if teste:
            break

        if not registros:
            if offset < total:
                raise RuntimeError(
                    "API retornou página vazia antes "
                    "de alcançar o total informado."
                )
            break

        offset += len(registros)
        numero_pagina += 1

        if offset >= total:
            break

        time.sleep(0.10)

    salvar_controle(
        ano=ano,
        mes=mes,
        total=total or 0,
        paginas=numero_pagina,
        teste=teste,
    )

    if not teste and total_baixado != (total or 0):
        raise RuntimeError(
            f"Quantidade baixada ({total_baixado}) "
            f"difere do total informado "
            f"pela API ({total})."
        )

    return total_baixado


def iterar_paginas():
    if not PASTA_RAW.exists():
        return

    yield from sorted(
        PASTA_RAW.glob(
            "*/*/pagina_*.json"
        )
    )


def consolidar():
    ARQUIVO_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivos = list(
        iterar_paginas() or []
    )

    if not arquivos:
        raise RuntimeError(
            "Nenhuma página de despesas "
            "foi encontrada para consolidar."
        )

    total_registros = 0

    with ARQUIVO_CSV.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo_saida:
        escritor = csv.DictWriter(
            arquivo_saida,
            fieldnames=COLUNAS,
            extrasaction="ignore",
        )

        escritor.writeheader()

        for arquivo_json in arquivos:
            conteudo = json.loads(
                arquivo_json.read_text(
                    encoding="utf-8"
                )
            )

            registros = conteudo.get(
                "registros",
                [],
            )

            for registro in registros:
                linha = {
                    coluna: registro.get(
                        coluna
                    )
                    for coluna in COLUNAS
                }

                escritor.writerow(
                    linha
                )

                total_registros += 1

    print(
        "\nConsolidação concluída:"
    )
    print(
        f"  páginas JSON: "
        f"{len(arquivos)}"
    )
    print(
        f"  registros CSV: "
        f"{total_registros}"
    )
    print(
        f"  arquivo: "
        f"{ARQUIVO_CSV}"
    )

    return total_registros


def validar_periodo(
    ano,
    mes=None,
):
    atual = datetime.now()

    if ano < ANO_INICIAL:
        raise ValueError(
            f"A fonte atual de despesas foi "
            f"confirmada a partir de {ANO_INICIAL}."
        )

    if ano > atual.year:
        raise ValueError(
            "Ano futuro não permitido."
        )

    if mes is not None:
        if mes < 1 or mes > 12:
            raise ValueError(
                "Mês deve estar entre 1 e 12."
            )

        if (
            ano == atual.year
            and mes > atual.month
        ):
            raise ValueError(
                "Mês futuro não permitido."
            )


def periodos(
    ano=None,
    mes=None,
):
    atual = datetime.now()

    if ano is not None:
        validar_periodo(
            ano,
            mes,
        )

        if mes is not None:
            yield ano, mes
            return

        ultimo_mes = (
            atual.month
            if ano == atual.year
            else 12
        )

        for numero_mes in range(
            1,
            ultimo_mes + 1,
        ):
            yield ano, numero_mes

        return

    for numero_ano in range(
        ANO_INICIAL,
        atual.year + 1,
    ):
        ultimo_mes = (
            atual.month
            if numero_ano == atual.year
            else 12
        )

        for numero_mes in range(
            1,
            ultimo_mes + 1,
        ):
            yield numero_ano, numero_mes


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Coleta despesas do Portal "
            "da Transparência de Palmas."
        )
    )

    parser.add_argument(
        "--ano",
        type=int,
        help="Ano específico para coleta.",
    )

    parser.add_argument(
        "--mes",
        type=int,
        help=(
            "Mês específico. "
            "Requer --ano."
        ),
    )

    parser.add_argument(
        "--teste",
        action="store_true",
        help=(
            "Baixa somente 5 registros "
            "do período selecionado."
        ),
    )

    parser.add_argument(
        "--somente-consolidar",
        action="store_true",
        help=(
            "Não acessa a API; consolida "
            "os JSONs já baixados."
        ),
    )

    args = parser.parse_args()

    if (
        args.mes is not None
        and args.ano is None
    ):
        parser.error(
            "--mes requer --ano"
        )

    if args.somente_consolidar:
        consolidar()
        return

    sessao = criar_sessao()

    try:
        for ano, mes in periodos(
            args.ano,
            args.mes,
        ):
            baixar_mes(
                sessao,
                ano,
                mes,
                teste=args.teste,
            )
    finally:
        sessao.close()

    consolidar()


if __name__ == "__main__":
    main()
