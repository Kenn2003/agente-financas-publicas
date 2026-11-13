import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


BASE = "https://acessoainformacao.palmas.to.gov.br"
PAGINA_PORTAL = f"{BASE}/cidadao/informacao/sglicitacoes"
API = f"{BASE}/api"

ACAO = "sglicitacoes/listar"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

RAIZ = Path(__file__).resolve().parents[3]

PASTA_JSON = (
    RAIZ
    / "data"
    / "raw"
    / "atualizacoes"
    / "licitacoes"
)

PASTA_CSV = RAIZ / "data" / "raw" / "csv"

ARQUIVO_CSV = PASTA_CSV / "atual_licitacoes.csv"

TAMANHO_PAGINA = 1000
PAUSA = 0.5
TENTATIVAS = 5


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    temporario = caminho.with_suffix(
        caminho.suffix + ".tmp"
    )

    with temporario.open(
        "w",
        encoding="utf-8"
    ) as arquivo:
        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    temporario.replace(caminho)


def criar_sessao():
    sessao = requests.Session()

    sessao.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
        }
    )

    resposta = sessao.get(
        PAGINA_PORTAL,
        timeout=30
    )

    resposta.raise_for_status()

    print(
        f"Portal acessado com sucesso "
        f"(HTTP {resposta.status_code})."
    )

    return sessao


def consultar(
    sessao,
    ano,
    offset,
    quantidade
):
    parametros = {
        "k1": {
            "order": {},
            "limit": f"{offset}, {quantidade}",
            "acao": ACAO,
            "ano": str(ano),
            "fracassadas_desertas": 0,
        }
    }

    dados_formulario = {
        "multi_request": "true",
        "params": json.dumps(
            parametros,
            ensure_ascii=False
        ),
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": (
            "application/x-www-form-urlencoded; "
            "charset=UTF-8"
        ),
        "Origin": BASE,
        "Referer": PAGINA_PORTAL,
        "Accept": "*/*",
    }

    ultimo_erro = None

    for tentativa in range(
        1,
        TENTATIVAS + 1
    ):
        try:
            resposta = sessao.post(
                API,
                data=dados_formulario,
                headers=headers,
                timeout=60,
            )

            resposta.raise_for_status()

            conteudo = resposta.json()

            bloco = conteudo.get("k1")

            if not isinstance(bloco, dict):
                raise ValueError(
                    "Resposta da API não possui "
                    "o bloco 'k1' esperado."
                )

            registros = bloco.get("dados")

            if not isinstance(registros, list):
                raise ValueError(
                    "Campo 'dados' da API "
                    "não é uma lista."
                )

            total = bloco.get("total", 0)

            try:
                total = int(total)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Total inválido retornado "
                    f"pela API: {total!r}"
                )

            return registros, total, bloco

        except (
            requests.RequestException,
            ValueError,
            json.JSONDecodeError,
        ) as erro:
            ultimo_erro = erro

            if tentativa == TENTATIVAS:
                break

            espera = 2 ** (tentativa - 1)

            print(
                f"Tentativa {tentativa} falhou: "
                f"{erro}. "
                f"Nova tentativa em "
                f"{espera}s..."
            )

            time.sleep(espera)

    raise RuntimeError(
        "Falha ao consultar licitações "
        f"após {TENTATIVAS} tentativas: "
        f"{ultimo_erro}"
    )


def baixar_ano(
    sessao,
    ano
):
    pasta_ano = PASTA_JSON / str(ano)

    pasta_ano.mkdir(
        parents=True,
        exist_ok=True
    )

    offset = 0
    pagina = 1
    total_esperado = None
    total_baixado = 0

    print(
        f"\nBaixando licitações de {ano}..."
    )

    while True:
        registros, total, bloco = consultar(
            sessao=sessao,
            ano=ano,
            offset=offset,
            quantidade=TAMANHO_PAGINA,
        )

        if total_esperado is None:
            total_esperado = total

            print(
                f"Total informado pela API: "
                f"{total_esperado}"
            )

        elif total != total_esperado:
            raise RuntimeError(
                "O total informado pela API "
                "mudou durante a coleta: "
                f"{total_esperado} -> {total}"
            )

        caminho = (
            pasta_ano
            / f"pagina_{pagina:06d}.json"
        )

        salvar_json(
            caminho,
            {
                "fonte": ACAO,
                "ano": ano,
                "offset": offset,
                "quantidade": TAMANHO_PAGINA,
                "total": total,
                "coletado_em": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
                "registros": registros,
            },
        )

        quantidade_recebida = len(registros)

        total_baixado += quantidade_recebida

        print(
            f"Página {pagina}: "
            f"{quantidade_recebida} registros "
            f"(acumulado: {total_baixado}/"
            f"{total_esperado})"
        )

        if quantidade_recebida == 0:
            break

        if total_baixado >= total_esperado:
            break

        offset += quantidade_recebida
        pagina += 1

        time.sleep(PAUSA)

    if total_baixado != total_esperado:
        raise RuntimeError(
            f"Coleta incompleta de {ano}: "
            f"API informou {total_esperado}, "
            f"mas foram baixados "
            f"{total_baixado}."
        )

    controle = {
        "fonte": ACAO,
        "ano": ano,
        "total": total_esperado,
        "paginas": pagina,
        "finalizado_em": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    salvar_json(
        pasta_ano / "controle.json",
        controle
    )

    print(
        f"Ano {ano} concluído: "
        f"{total_baixado} registros."
    )


def localizar_paginas():
    return sorted(
        PASTA_JSON.glob(
            "*/pagina_*.json"
        )
    )


def carregar_registros():
    registros = []

    arquivos = localizar_paginas()

    if not arquivos:
        raise FileNotFoundError(
            "Nenhuma página JSON de "
            "licitações foi encontrada."
        )

    for caminho in arquivos:
        with caminho.open(
            "r",
            encoding="utf-8"
        ) as arquivo:
            dados = json.load(arquivo)

        pagina_registros = dados.get(
            "registros"
        )

        if not isinstance(
            pagina_registros,
            list
        ):
            raise ValueError(
                f"'registros' inválido em "
                f"{caminho}"
            )

        registros.extend(
            pagina_registros
        )

    return registros


def identificar_colunas(registros):
    preferidas = [
        "tabela",
        "chave",
        "label",
        "numero",
        "numero_processo",
        "ano",
        "modalidade",
        "modalidade_sistema",
        "modalidade_id",
        "situacao",
        "situacao_id",
        "orgao",
        "orgao_id",
        "data_publicacao",
        "data_homologacao",
        "data_abertura",
        "data_fechamento",
        "data_protocolo",
        "data_julgamento",
        "valor_estimado",
        "valor_homologado",
        "descricao",
        "fundamento",
        "covid",
        "mp",
        "lei_base",
        "registro_preco",
        "lembretes",
        "orcamento_sigiloso",
        "ocultar_modalidades",
        "total",
        "empenhos",
    ]

    existentes = set()

    for registro in registros:
        existentes.update(
            registro.keys()
        )

    colunas = [
        coluna
        for coluna in preferidas
        if coluna in existentes
    ]

    extras = sorted(
        existentes - set(colunas)
    )

    return colunas + extras


def normalizar_valor(valor):
    if isinstance(valor, (dict, list)):
        return json.dumps(
            valor,
            ensure_ascii=False
        )

    return valor


def consolidar_csv():
    registros = carregar_registros()

    if not registros:
        raise RuntimeError(
            "Os arquivos JSON não possuem "
            "registros de licitações."
        )

    colunas = identificar_colunas(
        registros
    )

    PASTA_CSV.mkdir(
        parents=True,
        exist_ok=True
    )

    temporario = ARQUIVO_CSV.with_suffix(
        ".csv.tmp"
    )

    with temporario.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=colunas,
            extrasaction="ignore",
        )

        escritor.writeheader()

        for registro in registros:
            escritor.writerow(
                {
                    chave: normalizar_valor(
                        registro.get(chave)
                    )
                    for chave in colunas
                }
            )

    temporario.replace(
        ARQUIVO_CSV
    )

    print(
        f"\nCSV gerado com sucesso:"
    )
    print(ARQUIVO_CSV)
    print(
        f"Total de registros no CSV: "
        f"{len(registros)}"
    )


def testar_api(sessao, ano):
    registros, total, _ = consultar(
        sessao=sessao,
        ano=ano,
        offset=0,
        quantidade=5,
    )

    print(
        f"\nTeste da API de licitações:"
    )
    print(f"Ano: {ano}")
    print(f"Total na API: {total}")
    print(
        f"Registros recebidos: "
        f"{len(registros)}"
    )

    if registros:
        print(
            "\nCampos retornados:"
        )

        for campo in registros[0]:
            print(f"- {campo}")

        print(
            "\nPrimeiro registro:"
        )

        print(
            json.dumps(
                registros[0],
                ensure_ascii=False,
                indent=2
            )
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Coletor de licitações do "
            "Portal da Transparência "
            "de Palmas."
        )
    )

    parser.add_argument(
        "--ano",
        type=int,
        help=(
            "Coleta somente o ano "
            "informado."
        ),
    )

    parser.add_argument(
        "--teste",
        action="store_true",
        help=(
            "Consulta apenas 5 registros "
            "para validar a API."
        ),
    )

    parser.add_argument(
        "--somente-consolidar",
        action="store_true",
        help=(
            "Não baixa dados. "
            "Apenas gera o CSV a partir "
            "dos JSONs existentes."
        ),
    )

    args = parser.parse_args()

    if args.somente_consolidar:
        consolidar_csv()
        return

    ano_atual = datetime.now().year

    with criar_sessao() as sessao:
        if args.teste:
            testar_api(
                sessao,
                args.ano or ano_atual
            )
            return

        if args.ano:
            anos = [args.ano]
        else:
            anos = range(
                2021,
                ano_atual + 1
            )

        for ano in anos:
            baixar_ano(
                sessao,
                ano
            )

    consolidar_csv()


if __name__ == "__main__":
    main()
