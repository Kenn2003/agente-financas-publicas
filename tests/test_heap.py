import unittest
import pandas as pd

from src.data.loader import carregar_csvs, PASTA_DADOS, ARQUIVOS
from src.structures.heap import (
    criar_heap_prioridade,
    remover_maior_prioridade
)


class TestHeap(unittest.TestCase):

    def setUp(self):

        self.df = pd.DataFrame({
            "Nome": [
                "Empresa A",
                "Empresa B",
                "Empresa C"
            ],
            "Valor Total da Dívida": [
                "1.000,00",
                "5.000,00",
                "3.000,00"
            ],
            "Data da Inscrição": [
                "01/01/2026",
                "02/01/2026",
                "03/01/2026"
            ]
        })

    def test_quantidade_elementos(self):

        heap = criar_heap_prioridade(
            self.df,
            "Valor Total da Dívida",
            "Nome",
            "Data da Inscrição"
        )

        self.assertEqual(len(heap), 3)

    def test_maior_divida_primeiro(self):

        heap = criar_heap_prioridade(
            self.df,
            "Valor Total da Dívida",
            "Nome",
            "Data da Inscrição"
        )

        resultado = remover_maior_prioridade(heap)

        self.assertEqual(
            resultado["identificador"],
            "Empresa B"
        )

        self.assertEqual(
            resultado["prioridade"],
            5000.00
        )


if __name__ == "__main__":

    dataframes = carregar_csvs(
        PASTA_DADOS,
        ARQUIVOS
    )

    df_divida = dataframes["divida_ativa"]

    heap_dividas = criar_heap_prioridade(
        df_divida,
        coluna_prioridade="Valor Total da Dívida",
        coluna_identificador="Nome",
        coluna_data="Data da Inscrição"
    )

    print("Quantidade no heap:")
    print(len(heap_dividas))

    print("\n5 maiores prioridades:")

    for _ in range(5):
        print(
            remover_maior_prioridade(
                heap_dividas
            )
        )