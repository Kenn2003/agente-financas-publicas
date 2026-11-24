from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


FUNDAMENTO_LEGAL = (
    "LC Municipal 285/2013, art. 20, "
    "incisos II e III, §§ 1º e 2º"
)

# ==================================================
# 1. ENUMERAÇÕES
# ==================================================

class SituacaoBeneficio(str, Enum):

    RECONHECIDO = "reconhecido"
    PENDENTE = "pendente"
    NAO_RECONHECIDO = "nao_reconhecido"
    DESCONHECIDO = "desconhecido"


class DecisaoGovernanca(str, Enum):

    BLOQUEAR = "bloquear"
    REVISAO_HUMANA = "revisao_humana"
    PROSSEGUIR = "prosseguir_demais_controles"


class Elegibilidade(str, Enum):

    SIM = "sim"
    NAO = "nao"
    INDETERMINADA = "indeterminada"


# ==================================================
# 2. MODELO DE DADOS
# ==================================================

@dataclass(frozen=True)
class DadosContribuinte:

    exercicio: int

    situacao_beneficio: SituacaoBeneficio = (
        SituacaoBeneficio.DESCONHECIDO
    )

    dados_oficiais_verificados: bool = False

    pessoa_fisica: bool | None = None
    idade: int | None = None
    aposentado: bool | None = None
    pensionista: bool | None = None

    deficiencia_fisica_incapacitante: bool | None = None

    quantidade_imoveis: int | None = None
    quantidade_imoveis_edificados: int | None = None
    quantidade_edificacoes: int | None = None

    uso_exclusivamente_residencial: bool | None = None
    garagem_ou_box_autonomo: bool | None = None

    renda_mensal_sm: Decimal | None = None
    iptu_bruto_ufip: Decimal | None = None


@dataclass(frozen=True)
class ResultadoGovernanca:

    decisao: DecisaoGovernanca
    elegibilidade_pessoal: Elegibilidade
    elegibilidade_automatica: Elegibilidade
    motivo: str
    fundamento_legal: str = FUNDAMENTO_LEGAL


# ==================================================
# 3. LÓGICA TRIVALENTE
# ==================================================

def todos(criterios):

    if any(c is False for c in criterios):
        return Elegibilidade.NAO

    if all(c is True for c in criterios):
        return Elegibilidade.SIM

    return Elegibilidade.INDETERMINADA


def algum(criterios):

    if any(c is True for c in criterios):
        return True

    if all(c is False for c in criterios):
        return False

    return None


def comparar(valor, operador, limite):

    if valor is None:
        return None

    return operador(valor, limite)


# ==================================================
# 4. VALIDAÇÃO DOS DADOS
# ==================================================

def dados_validos(dados: DadosContribuinte):

    contagens = [
        dados.idade,
        dados.quantidade_imoveis,
        dados.quantidade_imoveis_edificados,
        dados.quantidade_edificacoes
    ]

    for valor in contagens:

        if valor is not None:
            if type(valor) is not int or valor < 0:
                return False

    monetarios = [
        dados.renda_mensal_sm,
        dados.iptu_bruto_ufip
    ]

    for valor in monetarios:

        if valor is not None:

            if not isinstance(valor, Decimal):
                return False

            if not valor.is_finite() or valor < 0:
                return False

    booleanos = [
        dados.pessoa_fisica,
        dados.aposentado,
        dados.pensionista,
        dados.deficiencia_fisica_incapacitante,
        dados.uso_exclusivamente_residencial,
        dados.garagem_ou_box_autonomo
    ]

    if any(
        v is not None and type(v) is not bool
        for v in booleanos
    ):
        return False

    if (
        dados.quantidade_imoveis is not None
        and dados.quantidade_imoveis_edificados is not None
        and dados.quantidade_imoveis_edificados
        > dados.quantidade_imoveis
    ):
        return False

    return True


# ==================================================
# 5. ISENÇÃO POR CONDIÇÃO PESSOAL
# ==================================================

def avaliar_isencao_pessoal(dados):

    categoria_pessoal = algum([
        comparar(
            dados.idade,
            lambda x, y: x > y,
            65
        ),
        dados.aposentado,
        dados.pensionista,
        dados.deficiencia_fisica_incapacitante
    ])

    criterios = [
        categoria_pessoal,

        comparar(
            dados.quantidade_imoveis_edificados,
            lambda x, y: x == y,
            1
        ),

        comparar(
            dados.renda_mensal_sm,
            lambda x, y: x <= y,
            Decimal("2")
        ),

        dados.uso_exclusivamente_residencial,

        comparar(
            dados.iptu_bruto_ufip,
            lambda x, y: x < y,
            Decimal("150")
        )
    ]

    return todos(criterios)


# ==================================================
# 6. ISENÇÃO AUTOMÁTICA
# ==================================================

def avaliar_isencao_automatica(dados):

    criterios = [
        dados.pessoa_fisica,

        comparar(
            dados.quantidade_imoveis,
            lambda x, y: x == y,
            1
        ),

        comparar(
            dados.quantidade_edificacoes,
            lambda x, y: x == y,
            1
        ),

        dados.uso_exclusivamente_residencial,

        comparar(
            dados.iptu_bruto_ufip,
            lambda x, y: x < y,
            Decimal("50")
        ),

        comparar(
            dados.garagem_ou_box_autonomo,
            lambda x, y: x == y,
            False
        )
    ]

    return todos(criterios)


# ==================================================
# 7. CAMADA DE GOVERNANÇA
# ==================================================

def avaliar_protecao_iptu_social(
    dados: DadosContribuinte
) -> ResultadoGovernanca:

    indeterminada = Elegibilidade.INDETERMINADA

    if (
        dados.dados_oficiais_verificados is True
        and dados.situacao_beneficio
        is SituacaoBeneficio.RECONHECIDO
    ):

        return ResultadoGovernanca(
            decisao=DecisaoGovernanca.BLOQUEAR,
            elegibilidade_pessoal=indeterminada,
            elegibilidade_automatica=indeterminada,
            motivo=(
                "Isenção tributária oficialmente "
                "reconhecida para o exercício."
            )
        )

    if not dados_validos(dados):

        return ResultadoGovernanca(
            decisao=DecisaoGovernanca.REVISAO_HUMANA,
            elegibilidade_pessoal=indeterminada,
            elegibilidade_automatica=indeterminada,
            motivo="Dados inválidos ou inconsistentes."
        )

    pessoal = avaliar_isencao_pessoal(dados)
    automatica = avaliar_isencao_automatica(dados)

    if (
        dados.dados_oficiais_verificados is not True

        or dados.situacao_beneficio
        is not SituacaoBeneficio.NAO_RECONHECIDO

        or pessoal is not Elegibilidade.NAO

        or automatica is not Elegibilidade.NAO
    ):

        return ResultadoGovernanca(
            decisao=DecisaoGovernanca.REVISAO_HUMANA,
            elegibilidade_pessoal=pessoal,
            elegibilidade_automatica=automatica,
            motivo=(
                "Possível benefício, situação pendente "
                "ou insuficiência de comprovação oficial."
            )
        )

    return ResultadoGovernanca(
        decisao=DecisaoGovernanca.PROSSEGUIR,
        elegibilidade_pessoal=pessoal,
        elegibilidade_automatica=automatica,
        motivo=(
            "Não foi identificada proteção pelos "
            "critérios avaliados. Aplicar os demais "
            "controles tributários antes de qualquer ação."
        )
    )
