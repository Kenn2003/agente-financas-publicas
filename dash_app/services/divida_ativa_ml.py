"""Interface restrita aos artefatos demonstrativos de ML da Dívida Ativa."""
from functools import lru_cache
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


RAIZ = Path(__file__).resolve().parents[2]
PASTA_MODELOS = RAIZ / "models"
STATUS_ALVO_SINTETICO = "sintetico_proxy_nao_observado"
FEATURES_PERMITIDAS = {"log_valor_divida", "idade_divida_dias"}


@lru_cache(maxsize=1)
def carregar_modelos():
    """Carrega uma vez apenas os artefatos documentados como sintéticos."""
    caminhos = {
        "baseline": PASTA_MODELOS / "baseline.joblib",
        "inadimplencia": PASTA_MODELOS / "inadimplencia.joblib",
        "recuperabilidade": PASTA_MODELOS / "recuperabilidade.joblib",
    }
    ausentes = [caminho.name for caminho in caminhos.values() if not caminho.is_file()]
    if ausentes:
        raise FileNotFoundError(", ".join(ausentes))

    pacotes = {nome: joblib.load(caminho) for nome, caminho in caminhos.items()}
    for nome, pacote in pacotes.items():
        if not isinstance(pacote, dict):
            raise ValueError(f"Pacote inválido: {nome}")
        if pacote.get("target_status") != STATUS_ALVO_SINTETICO:
            raise ValueError(f"O alvo do artefato {nome} não está identificado como sintético.")
        if not isinstance(pacote.get("data_referencia"), str):
            raise ValueError(f"Data de referência ausente no artefato {nome}.")
        try:
            pd.Timestamp(pacote["data_referencia"])
        except (TypeError, ValueError):
            raise ValueError(f"Data de referência inválida no artefato {nome}.") from None

        features = pacote.get("features")
        if not isinstance(features, list) or not features:
            raise ValueError(f"Features ausentes no artefato {nome}.")
        if set(features) != FEATURES_PERMITIDAS:
            raise ValueError(f"Features incompatíveis no artefato {nome}.")
        if nome == "baseline":
            estimadores = pacote.get("estimators")
            if not isinstance(estimadores, dict) or not estimadores:
                raise ValueError("Estimadores ausentes no artefato baseline.")
            if any(not hasattr(modelo, "predict_proba") for modelo in estimadores.values()):
                raise ValueError("Estimador incompatível no artefato baseline.")
        else:
            modelo = pacote.get("estimator")
            if not hasattr(modelo, "predict_proba") or not hasattr(modelo, "classes_"):
                raise ValueError(f"Estimador incompatível no artefato {nome}.")
    return pacotes


def informacoes_modelos():
    pacotes = carregar_modelos()
    referencias = {pd.Timestamp(pacote["data_referencia"]) for pacote in pacotes.values()}
    if len(referencias) != 1:
        raise ValueError("Os artefatos usam datas de referência diferentes.")
    referencia = next(iter(referencias))
    return {
        "data_referencia": referencia.date(),
        "features": ["log_valor_divida", "idade_divida_dias"],
        "aviso": pacotes["inadimplencia"].get(
            "aviso",
            "Os alvos são sintéticos e não representam resultados observados.",
        ),
    }


def diagnosticos_modelos():
    """Lê somente métricas agregadas já salvas nos artefatos do experimento."""
    pacotes = carregar_modelos()
    baseline = pacotes["baseline"]
    inadimplencia = pacotes["inadimplencia"]
    recuperabilidade = pacotes["recuperabilidade"]
    metricas_validacao = dict(baseline.get("validation_metrics", {}))
    metricas_validacao["random_forest"] = inadimplencia.get("validation_metrics", {})
    return {
        "metricas_validacao": metricas_validacao,
        "inadimplencia_teste": inadimplencia.get("test_metrics_proxy", {}),
        "recuperabilidade_teste": recuperabilidade.get("test_metrics_proxy", {}),
        "matriz_recuperabilidade": recuperabilidade.get("test_metrics_proxy", {}).get(
            "matriz_confusao_baixa_media_alta"
        ),
        "importancias": {
            nome: {
                feature: float(importance)
                for feature, importance in zip(
                    pacote["features"], pacote["estimator"].feature_importances_
                )
            }
            for nome, pacote in (
                ("inadimplencia", inadimplencia),
                ("recuperabilidade", recuperabilidade),
            )
        },
        "classes_recuperabilidade": ["baixa", "media", "alta"],
        "aviso": inadimplencia.get("aviso", "Rótulos sintéticos; sem desfechos observados."),
    }


def _montar_entrada(pacote, valor_divida, data_inscricao):
    valor = float(valor_divida)
    data = pd.Timestamp(data_inscricao)
    referencia = pd.Timestamp(pacote["data_referencia"])
    if not math.isfinite(valor) or valor < 0:
        raise ValueError("Informe um valor não negativo e válido.")
    if pd.isna(data):
        raise ValueError("Informe uma data de inscrição válida.")
    if data > referencia:
        raise ValueError("A data não pode ser posterior à referência dos modelos.")

    valores = {
        "log_valor_divida": float(np.log1p(valor)),
        "idade_divida_dias": max(0, int((referencia - data).days)),
    }
    features = pacote["features"]
    return pd.DataFrame([[valores[nome] for nome in features]], columns=features)


def simular(valor_divida, data_inscricao):
    """Executa os dois modelos em uma entrada hipotética, sem ler a base CSV."""
    pacotes = carregar_modelos()
    entrada = _montar_entrada(pacotes["inadimplencia"], valor_divida, data_inscricao)

    def probabilidades(modelo):
        probs = modelo.predict_proba(entrada)[0]
        return {str(classe): float(prob) for classe, prob in zip(modelo.classes_, probs)}

    saida = {
        nome: probabilidades(modelo)
        for nome, modelo in pacotes["baseline"]["estimators"].items()
    }
    saida["random_forest"] = probabilidades(pacotes["inadimplencia"]["estimator"])
    saida["recuperabilidade"] = probabilidades(pacotes["recuperabilidade"]["estimator"])

    if "1" not in saida["random_forest"]:
        raise ValueError("O artefato de inadimplência não contém a classe sintética 1.")
    return {
        "probabilidade_inadimplencia_proxy": saida["random_forest"]["1"],
        "probabilidades_inadimplencia_modelos": {
            nome: probs["1"] for nome, probs in saida.items()
            if nome != "recuperabilidade" and "1" in probs
        },
        "probabilidades_recuperabilidade_proxy": saida["recuperabilidade"],
        "data_referencia": pd.Timestamp(
            pacotes["inadimplencia"]["data_referencia"]
        ).date(),
    }


def curvas_sensibilidade(valor_divida, data_inscricao, pontos=25):
    """Varia valor e idade mantendo a outra entrada constante; não consulta a base."""
    valor = float(valor_divida)
    data = pd.Timestamp(data_inscricao)
    referencia = pd.Timestamp(informacoes_modelos()["data_referencia"])
    idade = max(0, int((referencia - data).days))
    base_valor = max(valor, 1.0)
    valores = np.geomspace(max(0.01, base_valor / 4), base_valor * 4, pontos)
    idades = np.linspace(max(0, idade - 730), min(idade + 730, 36500), pontos).round().astype(int)

    por_valor = {"valores": [], "modelos": {}, "recuperabilidade": {}}
    por_idade = {"idades": [], "modelos": {}, "recuperabilidade": {}}
    for nome in ("regressao_logistica", "arvore_decisao", "random_forest"):
        por_valor["modelos"][nome] = []
        por_idade["modelos"][nome] = []
    for classe in ("baixa", "media", "alta"):
        por_valor["recuperabilidade"][classe] = []
        por_idade["recuperabilidade"][classe] = []

    for quantia in valores:
        resultado = simular(quantia, data)
        por_valor["valores"].append(float(quantia))
        for nome, prob in resultado["probabilidades_inadimplencia_modelos"].items():
            por_valor["modelos"].setdefault(nome, []).append(prob)
        for classe, prob in resultado["probabilidades_recuperabilidade_proxy"].items():
            por_valor["recuperabilidade"].setdefault(classe.casefold(), []).append(prob)

    for dias in idades:
        data_ponto = (referencia - pd.Timedelta(days=int(dias))).date().isoformat()
        resultado = simular(valor, data_ponto)
        por_idade["idades"].append(int(dias))
        for nome, prob in resultado["probabilidades_inadimplencia_modelos"].items():
            por_idade["modelos"].setdefault(nome, []).append(prob)
        for classe, prob in resultado["probabilidades_recuperabilidade_proxy"].items():
            por_idade["recuperabilidade"].setdefault(classe.casefold(), []).append(prob)
    return {"valor": por_valor, "idade": por_idade}
