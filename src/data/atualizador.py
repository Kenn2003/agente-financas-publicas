import json
import time
import requests

from pathlib import Path
from datetime import datetime, timezone

BASE = "https://acessoainformacao.palmas.to.gov.br"
MODULO = "sgreceitas"
ACAO = "sgreceitas/listar"

NAVEGADOR = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

RAIZ = Path(__file__).resolve().parents[2]

PASTA_BASE = (
    RAIZ / "data" / "raw" / "atualizacoes" / "receitas"
)

TAMANHO_PAGINA = 1000
PAUSA = 0.5


def salvar_json(caminho, dados):
    """Salva JSON de forma atômica."""

    caminho.parent.mkdir(parents=True, exist_ok=True)

    temporario = caminho.with_suffix(".tmp")

    with open(temporario, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)

    temporario.replace(caminho)


def criar_sessao():

    sessao = requests.Session()

    sessao.headers.update({
        "User-Agent": NAVEGADOR
    })

    pagina = f"{BASE}/cidadao/transparencia/{MODULO}"

    resposta = sessao.get(pagina, timeout=60)
    resposta.raise_for_status()

    return sessao


def consultar(sessao, ano, mes, offset, quantidade):

    consulta = {
        "k1": {
            "order": {},
            "limit": f"{offset}, {quantidade}",
            "acao": ACAO,
            "ano": str(ano),
            "mes": str(mes)
        }
    }

    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": (
            "application/x-www-form-urlencoded; charset=UTF-8"
        ),
        "Referer": (
            f"{BASE}/cidadao/transparencia/{MODULO}"
        ),
        "Origin": BASE
    }

    for tentativa in range(1, 6):

        try:
            resposta = sessao.post(
                f"{BASE}/api",
                data={
                    "multi_request": "true",
                    "params": json.dumps(consulta)
                },
                headers=headers,
                timeout=90
            )

            resposta.raise_for_status()

            bloco = resposta.json().get("k1")

            if not isinstance(bloco, dict):
                raise ValueError(
                    f"Resposta inesperada: {bloco}"
                )

            registros = bloco.get("dados")

            if not isinstance(registros, list):
                raise ValueError(
                    "Campo 'dados' inválido."
                )

            total = int(bloco["total"])

            return registros, total

        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError
        ) as erro:

            if tentativa == 5:
                raise

            espera = 3 * (2 ** (tentativa - 1))

            print(
                f"Falha: {erro}. "
                f"Nova tentativa em {espera}s."
            )

            time.sleep(espera)


def baixar_mes(sessao, ano, mes, forcar=False):

    pasta = (
        PASTA_BASE
        / str(ano)
        / f"{mes:02d}"
    )

    pasta.mkdir(parents=True, exist_ok=True)

    controle = pasta / "controle.json"

    # Uma coleta completa anterior pode ser reutilizada.
    if controle.exists() and not forcar:
        with open(controle, encoding="utf-8") as f:
            estado = json.load(f)

        if estado.get("concluido"):
            arquivos = list(pasta.glob("pagina_*.json"))

            if (
                len(arquivos) == estado.get("paginas")
                and all(a.stat().st_size > 0 for a in arquivos)
            ):
                print(f"{ano}/{mes:02d}: já concluído.")
                return

    # Nova coleta: mantém snapshots anteriores em disco,
    # mas substitui os arquivos desta pasta.
    if forcar:
        for arquivo in pasta.glob("pagina_*.json"):
            arquivo.unlink()

        controle.unlink(missing_ok=True)

    offset = 0
    pagina = 1
    total_baixado = 0
    total_esperado = None

    while True:

        arquivo = pasta / f"pagina_{pagina:06d}.json"

        if arquivo.exists():

            with open(arquivo, encoding="utf-8") as f:
                dados = json.load(f)

            if (
                dados.get("offset") != offset
                or dados.get("quantidade") != TAMANHO_PAGINA
                or not isinstance(dados.get("registros"), list)
            ):
                raise ValueError(
                    f"Checkpoint inválido: {arquivo}"
                )

            registros = dados["registros"]
            total = int(dados["total"])

            print(f"{ano}/{mes:02d} página {pagina}: reutilizada")

        else:

            registros, total = consultar(
                sessao,
                ano,
                mes,
                offset,
                TAMANHO_PAGINA
            )

            dados = {
                "fonte": ACAO,
                "ano": ano,
                "mes": mes,
                "offset": offset,
                "quantidade": TAMANHO_PAGINA,
                "total": total,
                "coletado_em": datetime.now(
                    timezone.utc
                ).isoformat(),
                "registros": registros
            }

            salvar_json(arquivo, dados)

            print(
                f"{ano}/{mes:02d} página {pagina}: "
                f"{len(registros)} registros"
            )

        if total_esperado is None:
            total_esperado = total
        elif total != total_esperado:
            raise ValueError(
                "Total informado pela API mudou durante a coleta."
            )

        if not registros and total_baixado < total_esperado:
            raise ValueError(
                "A API retornou página vazia antes do fim."
            )

        total_baixado += len(registros)
        offset += TAMANHO_PAGINA
        pagina += 1

        if total_baixado >= total_esperado:
            break

        time.sleep(PAUSA)

    if total_baixado != total_esperado:
        raise ValueError(
            f"Total divergente: {total_baixado} "
            f"de {total_esperado}"
        )

    salvar_json(
        controle,
        {
            "concluido": True,
            "ano": ano,
            "mes": mes,
            "total": total_baixado,
            "paginas": pagina - 1,
            "finalizado_em": datetime.now(
                timezone.utc
            ).isoformat()
        }
    )

    print(
        f"Concluído {ano}/{mes:02d}: "
        f"{total_baixado} registros."
    )


def main():

    ano_atual = datetime.now().year
    mes_atual = datetime.now().month

    with criar_sessao() as sessao:

        for ano in range(2021, ano_atual + 1):

            ultimo_mes = (
                mes_atual if ano == ano_atual else 12
            )

            for mes in range(1, ultimo_mes + 1):

                baixar_mes(
                    sessao,
                    ano=ano,
                    mes=mes
                )



if __name__ == "__main__":
    main()
