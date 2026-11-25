"""Gera evidência reproduzível de explicabilidade para o RIA da Sprint 5.

A execução utiliza os artefatos versionados da Sprint 4 e um registro real
desidentificado do conjunto temporal de teste.

IMPORTANTE:
- Nome, CPF/CNPJ e outros identificadores não são utilizados.
- Os targets dos modelos são proxies sintéticos não observados.
- As probabilidades não devem ser interpretadas como risco real.
- Feature Importance é uma explicação GLOBAL do modelo, não uma decomposição
  da contribuição individual de cada variável para uma previsão específica.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn


ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = ROOT / "relatorio_dívida_ativa.csv"
MODELO_INAD = ROOT / "models" / "inadimplencia.joblib"
MODELO_REC = ROOT / "models" / "recuperabilidade.joblib"

SAIDA_DIR = ROOT / "docs" / "evidencias" / "explicabilidade"
SAIDA_JSON = SAIDA_DIR / "exemplo_real_anonimizado.json"
SAIDA_MD = SAIDA_DIR / "exemplo_real_anonimizado.md"

DATA_REFERENCIA = pd.Timestamp("2026-10-01")
FIM_VALIDACAO = pd.Timestamp("2026-06-30")


def carregar_registro_teste():
    """Reproduz a preparação da Sprint 4 sem carregar identificadores no modelo."""

    raw = pd.read_csv(
        DATA_PATH,
        sep=";",
        encoding="utf-8-sig",
    )

    colunas_obrigatorias = {
        "Valor Total da Dívida",
        "Data da Inscrição",
    }

    faltantes = colunas_obrigatorias.difference(raw.columns)

    if faltantes:
        raise ValueError(
            f"Colunas obrigatórias ausentes: {sorted(faltantes)}"
        )

    raw = raw.drop_duplicates()

    # Nenhum identificador pessoal é mantido nesta etapa.
    df = raw[
        ["Valor Total da Dívida", "Data da Inscrição"]
    ].copy()

    df["valor_divida"] = pd.to_numeric(
        df["Valor Total da Dívida"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )

    df["data_inscricao"] = pd.to_datetime(
        df["Data da Inscrição"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    df = (
        df.dropna(
            subset=["valor_divida", "data_inscricao"]
        )
        .loc[lambda x: x["valor_divida"] >= 0]
        .sort_values("data_inscricao")
        .reset_index(drop=True)
    )

    df["idade_divida_dias"] = (
        DATA_REFERENCIA - df["data_inscricao"]
    ).dt.days.clip(lower=0)

    df["log_valor_divida"] = np.log1p(
        df["valor_divida"]
    )

    teste = df[
        df["data_inscricao"] > FIM_VALIDACAO
    ].copy()

    if teste.empty:
        raise RuntimeError(
            "O conjunto temporal de teste está vazio."
        )

    # Seleção determinística do primeiro registro do conjunto de teste.
    registro = teste.iloc[[0]][
        ["log_valor_divida", "idade_divida_dias"]
    ].astype(float)

    return registro


def importar_importancias(artefato):
    modelo = artefato["estimator"]

    return {
        feature: round(float(importancia), 6)
        for feature, importancia in sorted(
            zip(
                artefato["features"],
                modelo.feature_importances_,
            ),
            key=lambda item: item[1],
            reverse=True,
        )
    }


def main():
    SAIDA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    registro = carregar_registro_teste()

    inad = joblib.load(MODELO_INAD)
    rec = joblib.load(MODELO_REC)

    modelo_inad = inad["estimator"]
    modelo_rec = rec["estimator"]

    pred_inad = int(
        modelo_inad.predict(registro)[0]
    )

    prob_inad = modelo_inad.predict_proba(
        registro
    )[0]

    pred_rec = str(
        modelo_rec.predict(registro)[0]
    )

    prob_rec = modelo_rec.predict_proba(
        registro
    )[0]

    probabilidades_rec = {
        str(classe): round(float(prob), 6)
        for classe, prob in zip(
            modelo_rec.classes_,
            prob_rec,
        )
    }

    resultado = {
        "evidencia": "registro_teste_anonimizado_001",
        "natureza_registro": (
            "Registro real da base, utilizado sem identificadores pessoais."
        ),
        "features_entrada": {
            "log_valor_divida": round(
                float(
                    registro.iloc[0][
                        "log_valor_divida"
                    ]
                ),
                4,
            ),
            "idade_divida_dias": int(
                registro.iloc[0][
                    "idade_divida_dias"
                ]
            ),
        },
        "inadimplencia_proxy": {
            "modelo": type(
                modelo_inad
            ).__name__,
            "classe_prevista": pred_inad,
            "probabilidades": {
                "classe_0": round(
                    float(prob_inad[0]),
                    6,
                ),
                "classe_1": round(
                    float(prob_inad[1]),
                    6,
                ),
            },
            "feature_importance_global": (
                importar_importancias(inad)
            ),
            "target_status": inad[
                "target_status"
            ],
        },
        "recuperabilidade_proxy": {
            "modelo": type(
                modelo_rec
            ).__name__,
            "classe_prevista": pred_rec,
            "probabilidades": (
                probabilidades_rec
            ),
            "feature_importance_global": (
                importar_importancias(rec)
            ),
            "target_status": rec[
                "target_status"
            ],
        },
        "governanca": {
            "aviso_modelo": inad["aviso"],
            "interpretacao_feature_importance": (
                "Feature Importance representa relevância global "
                "das variáveis no modelo e não a contribuição "
                "causal ou local de cada variável para esta previsão."
            ),
            "uso_operacional_autorizado": False,
        },
        "reprodutibilidade": {
            "data_referencia": (
                DATA_REFERENCIA.date().isoformat()
            ),
            "fim_validacao": (
                FIM_VALIDACAO.date().isoformat()
            ),
            "python_sklearn": sklearn.__version__,
        },
    }

    SAIDA_JSON.write_text(
        json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    imp_inad = resultado[
        "inadimplencia_proxy"
    ]["feature_importance_global"]

    imp_rec = resultado[
        "recuperabilidade_proxy"
    ]["feature_importance_global"]

    texto_md = f"""# Evidência de explicabilidade — Sprint 5

## Natureza do exemplo

Foi utilizado um registro real da base de dívida ativa pertencente ao conjunto
temporal de teste da Sprint 4. Nenhum nome, CPF/CNPJ ou outro identificador
pessoal é utilizado ou registrado nesta evidência.

## Entradas efetivamente utilizadas

- `log_valor_divida`: {resultado["features_entrada"]["log_valor_divida"]}
- `idade_divida_dias`: {resultado["features_entrada"]["idade_divida_dias"]}

## Modelo de inadimplência proxy

- Algoritmo: `{resultado["inadimplencia_proxy"]["modelo"]}`
- Classe prevista: `{pred_inad}`
- Probabilidade da classe 0: {prob_inad[0]:.4f}
- Probabilidade da classe 1: {prob_inad[1]:.4f}

### Feature Importance global

- `log_valor_divida`: {imp_inad["log_valor_divida"]:.4f} ({imp_inad["log_valor_divida"] * 100:.2f}%)
- `idade_divida_dias`: {imp_inad["idade_divida_dias"]:.4f} ({imp_inad["idade_divida_dias"] * 100:.2f}%)

## Modelo de recuperabilidade proxy

- Algoritmo: `{resultado["recuperabilidade_proxy"]["modelo"]}`
- Classe prevista: `{pred_rec}`

### Probabilidades

- Alta: {probabilidades_rec.get("alta", 0):.4f}
- Baixa: {probabilidades_rec.get("baixa", 0):.4f}
- Média: {probabilidades_rec.get("media", 0):.4f}

### Feature Importance global

- `log_valor_divida`: {imp_rec["log_valor_divida"]:.4f} ({imp_rec["log_valor_divida"] * 100:.2f}%)
- `idade_divida_dias`: {imp_rec["idade_divida_dias"]:.4f} ({imp_rec["idade_divida_dias"] * 100:.2f}%)

## Limitação metodológica

Os dois modelos possuem `target_status = sintetico_proxy_nao_observado`.
A base disponível não contém rótulos observados de pagamento, inadimplência
ou recuperação. Portanto, as probabilidades acima descrevem o comportamento
dos modelos experimentais e não podem ser interpretadas como probabilidades
reais relativas ao contribuinte.

A técnica de Feature Importance é utilizada como explicação global. Ela indica
a relevância das variáveis para o modelo como um todo, não a contribuição
individual ou causal de cada variável para esta previsão específica.

## Governança

> {inad["aviso"]}

O exemplo é exclusivamente demonstrativo e não autoriza priorização,
restrição de direitos ou decisão de cobrança sem revisão humana.
"""

    SAIDA_MD.write_text(
        texto_md,
        encoding="utf-8",
    )

    print("Evidência gerada com sucesso.")
    print("JSON:", SAIDA_JSON)
    print("Markdown:", SAIDA_MD)


if __name__ == "__main__":
    main()
