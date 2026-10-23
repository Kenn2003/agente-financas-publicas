"""Indicadores de qualidade; não elimina registros silenciosamente."""
import pandas as pd


def validar(df: pd.DataFrame, nome: str):
    if df.empty:
        raise ValueError(f'{nome}: base vazia; carga interrompida')
    if df.columns.duplicated().any():
        raise ValueError(f'{nome}: nomes de colunas duplicados')
    return {
        'base': nome,
        'linhas': int(len(df)),
        'colunas': int(len(df.columns)),
        'duplicadas_integralmente': int(df.duplicated().sum()),
        'nulos_por_coluna': {str(k): int(v) for k, v in df.isna().sum().items() if v > 0},
    }
