from decimal import Decimal

from src.governance.iptu_social import (
    DadosContribuinte,
    SituacaoBeneficio,
    avaliar_protecao_iptu_social
)


casos = {

    "Beneficiário reconhecido": DadosContribuinte(
        exercicio=2026,
        situacao_beneficio=SituacaoBeneficio.RECONHECIDO,
        dados_oficiais_verificados=True
    ),

    "Idoso potencialmente elegível": DadosContribuinte(
        exercicio=2026,
        idade=72,
        aposentado=True,
        quantidade_imoveis=1,
        quantidade_imoveis_edificados=1,
        quantidade_edificacoes=1,
        pessoa_fisica=True,
        renda_mensal_sm=Decimal("1.5"),
        iptu_bruto_ufip=Decimal("100"),
        uso_exclusivamente_residencial=True,
        garagem_ou_box_autonomo=False
    ),

    "Possível isenção automática": DadosContribuinte(
        exercicio=2026,
        pessoa_fisica=True,
        quantidade_imoveis=1,
        quantidade_edificacoes=1,
        uso_exclusivamente_residencial=True,
        garagem_ou_box_autonomo=False,
        iptu_bruto_ufip=Decimal("45")
    ),

    "Contribuinte sem dados": DadosContribuinte(
        exercicio=2026
    ),

    "Contribuinte sem enquadramento": DadosContribuinte(
        exercicio=2026,
        situacao_beneficio=(
            SituacaoBeneficio.NAO_RECONHECIDO
        ),
        dados_oficiais_verificados=True,
        idade=40,
        aposentado=False,
        pensionista=False,
        deficiencia_fisica_incapacitante=False,
        pessoa_fisica=True,
        quantidade_imoveis=3,
        quantidade_imoveis_edificados=3,
        quantidade_edificacoes=1,
        renda_mensal_sm=Decimal("8"),
        iptu_bruto_ufip=Decimal("300"),
        uso_exclusivamente_residencial=True,
        garagem_ou_box_autonomo=False
    )
}


for nome, dados in casos.items():

    resultado = avaliar_protecao_iptu_social(dados)

    print("=" * 60)
    print("CASO:", nome)
    print("Decisão:", resultado.decisao.value)
    print("Isenção pessoal:",
          resultado.elegibilidade_pessoal.value)
    print("Isenção automática:",
          resultado.elegibilidade_automatica.value)
    print("Motivo:", resultado.motivo)
    print("Base legal:", resultado.fundamento_legal)
