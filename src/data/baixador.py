import json
import time
import requests
import urllib3

from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE = "https://integracao.palmas.to.gov.br/apirest/"

ENDPOINTS = {
    "gastos_diretos": "gastos-diretos/",
    "arrecadacao": "arrecadacao/",
    "folha_pagamento": "folha-pagamento/"
}

RAIZ = Path(__file__).resolve().parents[2]
PASTA_BASE = RAIZ / "data" / "raw" / "historico"

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


def validar_url(url):
    """Impede que a paginação acesse outro domínio."""
    destino = urlparse(url)

    if (
        destino.scheme not in ("http", "https")
        or destino.hostname != "integracao.palmas.to.gov.br"
        or destino.port not in (None, 80, 443)
        or not destino.path.startswith("/apirest/")
        or destino.username is not None
        or destino.password is not None
    ):
        raise ValueError(f"URL não permitida: {url}")
        
    url_segura = destino._replace(
        scheme = 'https',
        netloc = "integracao.palmas.to.gov.br"
        ).geturl()

    return url_segura


def baixar_base(nome, endpoint, limite_paginas=5):

    pasta = PASTA_BASE / nome
    pasta.mkdir(parents=True, exist_ok=True)

    url = BASE + endpoint
    pagina = 1
    total_registros = 0

    with requests.Session() as sessao:

        while url and (
            limite_paginas is None
            or pagina <= limite_paginas
        ):

            url = validar_url(url)
            arquivo = pasta / f"pagina_{pagina:06d}.json"

            if arquivo.exists():

                with open(arquivo, encoding="utf-8") as f:
                    dados = json.load(f)

                print(f"[{nome}] Página {pagina} já existe.")

            else:

                for tentativa in range(3):
                    try:
                        resposta = sessao.get(
                            url,
                            timeout=60,
                            verify=False
                        )

                        resposta.raise_for_status()
                        dados = resposta.json()

                        if not isinstance(dados.get("results"), list):
                            raise ValueError("Resposta JSON inválida")

                        temporario = arquivo.with_suffix(".tmp")

                        with open(
                            temporario, "w", encoding="utf-8"
                        ) as f:
                            json.dump(
                                dados,
                                f,
                                ensure_ascii=False
                            )

                        temporario.replace(arquivo)
                        break

                    except (requests.RequestException, ValueError):
                        if tentativa == 2:
                            raise

                        time.sleep(2 ** (tentativa + 1))

                print(
                    f"[{nome}] Página {pagina}: "
                    f"{len(dados['results'])} registros"
                )

                time.sleep(0.3)

            total_registros += len(dados["results"])

            proxima = dados.get("next")

            url = (
                urljoin(url, proxima)
                if proxima
                else None
            )

            pagina += 1

    print(
        f"\n{nome}: {total_registros} registros "
        "processados nesta execução.\n"
    )


def main():

    for nome, endpoint in ENDPOINTS.items():

        print(f"\nIniciando: {nome}")

        baixar_base(
            nome=nome,
            endpoint=endpoint,
            limite_paginas=None
        )


if __name__ == "__main__":
    main()
