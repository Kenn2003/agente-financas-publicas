from .iptu_social import (
    DadosContribuinte,
    SituacaoBeneficio,
    DecisaoGovernanca,
    avaliar_protecao_iptu_social
)


class CobrancaNaoAutorizada(PermissionError):
    """Operação bloqueada pela política de governança."""


def verificar_protecao_iptu_social(
    exercicio: int
) -> dict:
    """
    Consulta a política de proteção ao IPTU Social.

    A base atual não possui registros administrativos
    que permitam verificar benefícios individuais.

    Esta função não concede isenções nem autoriza
    operações de cobrança.
    """

    if type(exercicio) is not int or exercicio != 2026:

        return {
            "decisao": "revisao_humana",
            "cobranca_autorizada": False,
            "motivo": (
                "Exercício fora do escopo das regras "
                "atualmente implementadas."
            )
        }

    dados = DadosContribuinte(
        exercicio=exercicio,
        situacao_beneficio=(
            SituacaoBeneficio.DESCONHECIDO
        ),
        dados_oficiais_verificados=False
    )

    resultado = avaliar_protecao_iptu_social(dados)

    return {
        "exercicio": exercicio,
        "decisao": resultado.decisao.value,
        "cobranca_autorizada": False,
        "dados_oficiais_verificados": False,
        "elegibilidade_pessoal": (
            resultado.elegibilidade_pessoal.value
        ),
        "elegibilidade_automatica": (
            resultado.elegibilidade_automatica.value
        ),
        "motivo": resultado.motivo,
        "fundamento_legal": resultado.fundamento_legal,
        "limitacao": (
            "A base atual não permite verificar "
            "a elegibilidade individual ao IPTU Social."
        )
    }


def exigir_liberacao_governanca(
    dados: DadosContribuinte
) -> None:
    """
    Barreira para futuras operações individualizadas.

    Não substitui os demais controles tributários.
    Os dados devem vir de fonte administrativa confiável,
    nunca de argumentos fornecidos pelo LLM.
    """

    if type(dados.exercicio) is not int:
        raise CobrancaNaoAutorizada(
            "Exercício tributário inválido."
        )

    if dados.exercicio != 2026:
        raise CobrancaNaoAutorizada(
            "Exercício fora do escopo da política."
        )

    resultado = avaliar_protecao_iptu_social(dados)

    if resultado.decisao != DecisaoGovernanca.PROSSEGUIR:

        raise CobrancaNaoAutorizada(
            resultado.motivo
        )
