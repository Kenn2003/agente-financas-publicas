import requests
import urllib3

URL_ANTIGA = (
    "https://integracao.palmas.to.gov.br/"
    "apirest/gastos-diretos/"
)


def testar_api_antiga():

    # Suprime avisos apenas neste teste diagnóstico
    urllib3.disable_warnings(
        urllib3.exceptions.InsecureRequestWarning
    )

    resposta = requests.get(
        URL_ANTIGA,
        timeout=60,
        verify=False  # Somente para diagnóstico
    )

    resposta.raise_for_status()

    dados = resposta.json()

    print("Status HTTP:", resposta.status_code)
    print("URL final:", resposta.url)
    print("Total de registros:", dados.get("count"))
    print("Próxima página:", dados.get("next"))

    registros = dados.get("results", [])

    print("Registros recebidos:", len(registros))

    if registros:
        print("Colunas:", list(registros[0].keys()))
        print("Primeiro registro:", registros[0])

    return dados


if __name__ == "__main__":
    testar_api_antiga()
