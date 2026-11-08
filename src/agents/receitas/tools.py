from pathlib import Path
import pandas as pd
import unicodedata

# Caminho relativo à raiz do repositório
RAIZ = Path(__file__).resolve().parents[3]
ARQUIVO = RAIZ / "data" / "processed" / "receitas_recentes.csv"

COLUNAS = [
    "ano", "mes","orgao", "orgao_nome",
    "codigo", "valor_arrecado_mes"
]

# Apenas categorias de primeiro nível.
CODIGOS_TOTAL = {
    "1.0.0.0.00.0.0",
    "2.0.0.0.00.0.0",
    "7.0.0.0.00.0.0",
    "8.0.0.0.00.0.0",
}


def carregar_receitas():
    """Carrega somente as colunas necessárias."""
    if not ARQUIVO.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {ARQUIVO}"
        )


    df = pd.read_csv(
        ARQUIVO,
        usecols=COLUNAS,
        dtype={"codigo": "string"},
        low_memory=False
    )

    df["valor_arrecado_mes"] = pd.to_numeric(
        df["valor_arrecado_mes"],
        errors="coerce"
    )

    df = df[df["codigo"].isin(CODIGOS_TOTAL)].copy()

    return df


def filtrar_receitas(
    df,
    ano,
    mes=None,
    orgao=None,
    codigo_orgao=None
):
    resultado = df[df["ano"] == int(ano)]

    if mes is not None:
        mes = int(mes)
        if not 1 <= mes <= 12:
            raise ValueError("O mês deve estar entre 1 e 12.")
        resultado = resultado[resultado["mes"] == mes]

    if codigo_orgao is not None:
        resultado = resultado[
            pd.to_numeric(
                resultado["orgao"], errors="coerce"
            ) == int(codigo_orgao)
        ]

    if orgao is not None:
        resultado = resultado[
            resultado["orgao_nome"].fillna("").str.casefold()
            == str(orgao).casefold()
        ]

    return resultado



def consultar_receitas(
        ano, 
        mes: int = None,
        orgao: str = None,
        codigo_orgao: int = None
        ):
    """Consulta o total arrecadado no período."""
    
    df = carregar_receitas()
    df_filtrado = filtrar_receitas(
        df,
        ano=ano,
        mes=mes,
        orgao=orgao,
        codigo_orgao=codigo_orgao
    )
    
    dados = df_filtrado

    if dados.empty:
        return {"status": "sem_dados"}

    return {
        "status": "ok",
        "ano": int(ano),
        "mes": mes,
        "orgao": orgao,
        "codigo_orgao": codigo_orgao,
        "valor_arrecadado": round(
            float(dados["valor_arrecado_mes"].sum()), 2
        ),
        "meses_encontrados": sorted(
            dados["mes"].unique().tolist()
        ),
        "fonte": "receitas_recentes.csv",
        "criterio": "classificacoes de primeiro nivel",
        "validacao_oficial": "pendente"
    }


def evolucao_arrecadacao(ano, orgao=None):
    """Retorna os valores mensais de um ano."""
    df = carregar_receitas()
    dados = filtrar_receitas(df, ano, orgao=orgao)

    if dados.empty:
        return {"status": "sem_dados"}

    mensal = (
        dados.groupby("mes")["valor_arrecado_mes"]
        .sum()
        .sort_index()
    )

    return {
        "status": "ok",
        "ano": int(ano),
        "orgao": orgao,
        "evolucao": [
            {"mes": int(m), "valor": round(float(v), 2)}
            for m, v in mensal.items()
        ],
        "validacao_oficial": "pendente"
    }


def comparar_periodos(ano_inicial, ano_final, orgao=None):
    """Compara anos usando somente meses comuns."""
    df = carregar_receitas()

    a = filtrar_receitas(df, ano_inicial, orgao=orgao)
    b = filtrar_receitas(df, ano_final, orgao=orgao)

    meses = sorted(set(a["mes"]) & set(b["mes"]))

    if not meses:
        return {"status": "sem_periodos_comparaveis"}

    valor_a = float(
        a.loc[a["mes"].isin(meses), "valor_arrecado_mes"].sum()
    )
    valor_b = float(
        b.loc[b["mes"].isin(meses), "valor_arrecado_mes"].sum()
    )

    variacao = (
        ((valor_b / valor_a) - 1) * 100
        if valor_a != 0 else None
    )

    return {
        "status": "ok",
        "ano_inicial": int(ano_inicial),
        "ano_final": int(ano_final),
        "meses_comparados": meses,
        "valor_inicial": round(valor_a, 2),
        "valor_final": round(valor_b, 2),
        "variacao_percentual": (
            round(variacao, 2)
            if variacao is not None else None
        ),
        "validacao_oficial": "pendente"
    }


def normalizar_texto(texto):
    texto = str(texto).casefold().strip()

    return "".join(
        caractere
        for caractere in unicodedata.normalize(
            "NFKD", texto
        )
        if not unicodedata.combining(caractere)
    )



def buscar_orgaos(
    termo: str,
    ano: int = None
) -> dict:
    """Busca órgãos por nome, com filtro opcional de ano."""

    if not isinstance(termo, str) or not termo.strip():
        return {
            "status": "termo_invalido",
            "orgaos": []
        }

    df = pd.read_csv(
        ARQUIVO,
        usecols=["ano", "orgao", "orgao_nome"],
        low_memory=False
    )

    if ano is not None:
        df = df[df["ano"] == int(ano)]

    df = df.drop_duplicates(
        subset=["orgao", "orgao_nome"]
    )

    termo_normalizado = normalizar_texto(termo)

    nomes = df["orgao_nome"].fillna(
        ""
    ).map(normalizar_texto)

    encontrados = df[
        nomes.str.contains(
            termo_normalizado,
            regex=False
        )
    ].sort_values("orgao_nome")

    return {
        "status": (
            "ok" if not encontrados.empty
            else "sem_correspondencia"
        ),
        "ano": ano,
        "total": len(encontrados),
        "orgaos": encontrados[
            ["orgao", "orgao_nome"]
        ].to_dict(orient="records")
    }


