import json
import requests

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

    # Inicializa a sessão do portal
    resposta = sessao.get(
        pagina,
        headers={"User-Agent": NAVEGADOR},
        timeout=60
    )
    resposta.raise_for_status()

    consulta = {
        "k1": {
            "order": {},
            "limit": "0, 1",
            "acao": "sgreceitas/listar",
            "ano": "2025",
            "mes": "7"
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
        raise ValueError(f"Resposta inesperada: {bloco}")

    print("Total:", bloco.get("total"))

    registros = bloco.get("dados") or []

    if registros:
        print("Campos:", list(registros[0].keys()))
        print("Primeiro registro:", registros[0])

    return registros


if __name__ == "__main__":
    testar_api_nova()
