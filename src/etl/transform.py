"""Transformações conservadoras: não inferir dados ausentes."""
import pandas as pd


def _numero(serie):
    s = serie.astype('string').str.strip().str.replace(r'\s+', '', regex=True)
    # Apenas quando há vírgula decimal, remover pontos de milhar.
    tem_virgula = s.str.contains(',', regex=False, na=False)
    s = s.where(~tem_virgula, s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False))
    return pd.to_numeric(s, errors='coerce')


def transformar(df, nome):
    """Devolve cópia tratada e contagens de conversões malsucedidas."""
    saida = df.copy()
    saida.columns = saida.columns.str.strip()
    relatorio = {'base': nome, 'linhas_entrada': len(saida), 'colunas_entrada': len(saida.columns), 'conversoes_invalidas': {}}
    saida = saida.dropna(axis=1, how='all')
    for coluna in saida.columns:
        c = coluna.lower()
        if c.startswith(('valor_', 'vencimento_', 'desconto_')) or c == 'receita_valor':
            original = saida[coluna]
            convertido = _numero(original)
            invalidos = int((original.notna() & original.astype('string').str.strip().ne('') & convertido.isna()).sum())
            relatorio['conversoes_invalidas'][coluna] = invalidos
            saida[coluna] = convertido
        elif c.startswith('data_') or c in ('data', 'receita_data_ocorrencia'):
            original = saida[coluna]
            convertido = pd.to_datetime(
                original,
                errors="coerce",
                format="mixed",
                dayfirst=False
            )
            invalidos = int((original.notna() & original.astype('string').str.strip().ne('') & convertido.isna()).sum())
            relatorio['conversoes_invalidas'][coluna] = invalidos
            saida[coluna] = convertido
    return saida, relatorio
