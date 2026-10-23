import json
import time
import requests
import pandas as pd

BASE = "https://acessoainformacao.palmas.to.gov.br"

NAVEGADOR = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def testar_api_nova():

    sessao = requests.Session()

    pagina = f"{BASE}/cidadao/transparencia/sgreceitas"

    resposta = sessao.get(
        pagina,
        headers={"User-Agent": NAVEGADOR},
        timeout=60
    )
    resposta.raise_for_status()

    todos_registros = []
    limite = 1000

    for mes in range(1, 13):

        inicio = 0
        pagina_atual = 1
        registros_mes = []

        while True:

            consulta = {
                "k1": {
                    "order": {},
                    "limit": f"{inicio}, {limite}",
                    "acao": "sgreceitas/listar",
                    "ano": "2024",
                    "mes": str(mes)
                }
            }

            resposta = sessao.post(
                f"{BASE}/api",
                data={
                    "multi_request": "true",
                    "params": json.dumps(consulta)
                },
                headers={
                    "User-Agent": NAVEGADOR,
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": pagina,
                    "Origin": BASE
                },
                timeout=60
            )

            resposta.raise_for_status()

            bloco = resposta.json()["k1"]

            if not isinstance(bloco, dict):
                raise ValueError(
                    f"Resposta inesperada: {bloco}"
                )

            registros = bloco.get("dados") or []

            total = int(bloco.get("total") or 0)

            if not registros:
                if total and inicio < total:
                    raise RuntimeError(
                        f"Paginação interrompida em 2024/{mes:02d}: "
                        f"{inicio} de {total} registros."
                    )
                break

            registros_mes.extend(registros)

            print(
                f"2024/{mes:02d} página {pagina_atual}: "
                f"{len(registros)} registros"
            )

            inicio += len(registros)
            pagina_atual += 1

            if total and len(registros_mes) >= total:
                break

            if not total and len(registros) < limite:
                break

            time.sleep(0.3)

        todos_registros.extend(registros_mes)

        print(
            f"Concluído 2024/{mes:02d}: "
            f"{len(registros_mes)} registros."
        )

    print("\nTotal de registros em 2024:", len(todos_registros))

    if todos_registros:
        print("Campos:", list(todos_registros[0].keys()))
        print("Primeiro registro:", todos_registros[0])

    return todos_registros


if __name__ == "__main__":

    registros = testar_api_nova()

    df = pd.DataFrame(registros)

    df.to_csv(
        "receitas_2024.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nArquivo receitas_2024.csv salvo.")