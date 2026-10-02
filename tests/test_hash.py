import unittest
import pandas as pd

from src.structures.hash_index import (
    criar_indice_hash,
    buscar_indice
)


class TestHash(unittest.TestCase):

    def setUp(self):

        self.df = pd.DataFrame({
            "cpf_cnpj": [
                "11111111000100",
                "22222222000100",
                "11111111000100"
            ],
            "fornecedor": [
                "Empresa A",
                "Empresa B",
                "Empresa A"
            ],
            "valor_pago": [
                1000.00,
                2000.00,
                3000.00
            ]
        })

    def test_criar_indice(self):

        indice = criar_indice_hash(
            self.df,
            "cpf_cnpj"
        )

        # Existem 3 registros, mas apenas 2 chaves distintas
        self.assertEqual(len(indice), 2)

    def test_multiplos_registros_mesma_chave(self):

        indice = criar_indice_hash(
            self.df,
            "cpf_cnpj"
        )

        resultado = buscar_indice(
            indice,
            "11111111000100"
        )

        # Empresa A possui dois registros
        self.assertEqual(len(resultado), 2)

    def test_buscar_chave_existente(self):

        indice = criar_indice_hash(
            self.df,
            "cpf_cnpj"
        )

        resultado = buscar_indice(
            indice,
            "22222222000100"
        )

        self.assertEqual(
            resultado[0]["fornecedor"],
            "Empresa B"
        )

        self.assertEqual(
            resultado[0]["valor_pago"],
            2000.00
        )

    def test_buscar_chave_inexistente(self):

        indice = criar_indice_hash(
            self.df,
            "cpf_cnpj"
        )

        resultado = buscar_indice(
            indice,
            "99999999000100"
        )

        self.assertEqual(resultado, [])


if __name__ == "__main__":
    unittest.main()
    
    
    