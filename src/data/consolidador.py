from pathlib import Path
import csv
import json

RAIZ = Path(__file__).resolve().parents[2]

PASTA_HISTORICO = (
    RAIZ / "data" / "raw" / "historico"
)

PASTA_CSV = (
    RAIZ / "data" / "raw" / "csv"
)


def localizar_arquivos(nome_base):

    pasta = PASTA_HISTORICO / nome_base

    arquivos = sorted(
        pasta.glob("pagina_*.json")
    )

    return arquivos

def ler_json(caminho):

    with open(caminho, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    registros = dados.get("results")

    if not isinstance(registros, list):
        raise ValueError(
            f"JSON sem lista 'results': {caminho}"
        )

    return registros


def consolidar_base(nome_base):

    arquivos = localizar_arquivos(nome_base)

    registros_consolidados = []

    for arquivo in arquivos:

        registros = ler_json(arquivo)

        registros_consolidados.extend(registros)

        print(
            f"{arquivo.name}: "
            f"{len(registros)} registros"
        )

    return registros_consolidados


def salvar_csv(registros, nome_base):

    if not registros:
        print("Nenhum registro para salvar.")
        return

    PASTA_CSV.mkdir(parents=True, exist_ok=True)

    caminho = PASTA_CSV / f"historico_{nome_base}.csv"

    colunas = list(
        dict.fromkeys(
            chave
            for registro in registros
            for chave in registro.keys()
        )
    )

    with open(
        caminho,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=colunas,
            delimiter=","
        )

        escritor.writeheader()
        escritor.writerows(registros)

    print(f"\nCSV salvo em: {caminho}")
    print(f"Registros exportados: {len(registros)}")
    print(f"Colunas exportadas: {len(colunas)}")

def identificar_colunas(arquivos):

    colunas = []

    for arquivo in arquivos:

        registros = ler_json(arquivo)

        for registro in registros:

            for coluna in registro.keys():

                if coluna not in colunas:
                    colunas.append(coluna)

    return colunas

def consolidar_csv(nome_base):

    arquivos = localizar_arquivos(nome_base)

    if not arquivos:
        print(f"Nenhum arquivo encontrado: {nome_base}")
        return

    colunas = identificar_colunas(arquivos)

    PASTA_CSV.mkdir(
        parents=True,
        exist_ok=True
    )

    destino = (
        PASTA_CSV / f"historico_{nome_base}.csv"
    )

    total = 0

    with open(
        destino,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo_csv:

        escritor = csv.DictWriter(
            arquivo_csv,
            fieldnames=colunas,
            delimiter=","
        )

        escritor.writeheader()

        for arquivo_json in arquivos:

            registros = ler_json(arquivo_json)

            escritor.writerows(registros)

            total += len(registros)

            print(
                f"{arquivo_json.name}: "
                f"{len(registros)} registros"
            )

    print(f"\nBase: {nome_base}")
    print(f"Total exportado: {total}")
    print(f"Colunas: {len(colunas)}")
    print(f"Destino: {destino}")


def verificar_paginas(arquivos):

    if not arquivos:
        raise ValueError("Nenhuma página encontrada.")

    total_registros = 0
    total_esperado = None

    for numero, arquivo in enumerate(arquivos, start=1):

        nome_esperado = f"pagina_{numero:06d}.json"

        if arquivo.name != nome_esperado:
            raise ValueError(
                f"Página ausente ou fora de ordem: {nome_esperado}"
            )

        with open(arquivo, encoding="utf-8") as f:
            dados = json.load(f)

        if not isinstance(dados.get("results"), list):
            raise ValueError(
                f"JSON inválido: {arquivo.name}"
            )

        quantidade = len(dados["results"])

        if total_esperado is None:
            total_esperado = int(dados["count"])

        total_registros += quantidade

    if total_registros != total_esperado:
        raise ValueError(
            f"Coleta incompleta: {total_registros} "
            f"de {total_esperado} registros."
        )

    print(
        f"Coleta validada: {total_registros} registros."
    )

    return total_registros



def consolidar_receitas_recentes():

    origem = RAIZ / "data" / "raw" / "atualizacoes" / "receitas"

    arquivos = sorted(origem.glob("*/*/pagina_*.json"))

    if not arquivos:
        print("Nenhuma receita recente encontrada.")
        return

    PASTA_CSV.mkdir(parents=True, exist_ok=True)

    destino = PASTA_CSV / "atual_receitas.csv"
    temporario = destino.with_suffix(".csv.tmp")

    colunas = [
        "total",
        "orgao_nome",
        "unidade_nome",
        "codigo",
        "orgao",
        "ano",
        "mes",
        "descricao",
        "valor_orcado",
        "valor_arrecado_mes",
        "valor_arrecado_periodo",
        "covid",
        "unidade_id",
        "codigo_original"
    ]

    total_registros = 0
    meses_processados = set()
    totais_mensais = {}

    try:
        with open(
            temporario,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as csv_saida:

            escritor = csv.DictWriter(
                csv_saida,
                fieldnames=colunas,
                delimiter=","
            )

            escritor.writeheader()

            for caminho in arquivos:

                ano_pasta = int(caminho.parent.parent.name)
                mes_pasta = int(caminho.parent.name)

                with open(
                    caminho,
                    "r",
                    encoding="utf-8"
                ) as arquivo:
                    dados = json.load(arquivo)

                registros = dados.get("registros")

                if not isinstance(registros, list):
                    raise ValueError(
                        f"Registros inválidos: {caminho}"
                    )

                if (
                    int(dados.get("ano")) != ano_pasta
                    or int(dados.get("mes")) != mes_pasta
                ):
                    raise ValueError(
                        f"Metadados inconsistentes: {caminho}"
                    )

                for registro in registros:

                    if (
                        int(registro.get("ano")) != ano_pasta
                        or int(registro.get("mes")) != mes_pasta
                    ):
                        raise ValueError(
                            f"Período inconsistente: {caminho}"
                        )

                    escritor.writerow(registro)

                periodo = (ano_pasta, mes_pasta)

                meses_processados.add(periodo)

                total_registros += len(registros)

                totais_mensais[periodo] = (
                    totais_mensais.get(periodo, 0)
                    + len(registros)
                )

        temporario.replace(destino)

    except Exception:
        temporario.unlink(missing_ok=True)
        raise

    print("\nCONSOLIDAÇÃO DAS RECEITAS RECENTES")
    print(f"Arquivos processados: {len(arquivos)}")
    print(f"Meses encontrados: {len(meses_processados)}")
    print(f"Registros exportados: {total_registros}")
    print(f"Colunas: {len(colunas)}")
    print(f"CSV salvo em: {destino}")

    print("\nREGISTROS POR ANO")

    anos = sorted(
        {ano for ano, mes in meses_processados}
    )

    for ano in anos:

        quantidade = sum(
            total
            for (ano_registro, mes), total
            in totais_mensais.items()
            if ano_registro == ano
        )

        print(f"{ano}: {quantidade} registros")



if __name__ == "__main__":

    for nome_base in [
        "arrecadacao",
        "gastos_diretos",
        "folha_pagamento"
    ]:
       consolidar_csv(nome_base)

    consolidar_receitas_recentes()







