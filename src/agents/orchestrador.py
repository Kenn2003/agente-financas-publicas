import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
import time
from google.genai import errors

from src.agents.prompts_orchestrador import (
    PROMPT_ROTEAMENTO,
    PROMPT_SINTESE,
)

from src.agents.receitas.agent import AgenteReceitas
from src.agents.despesas.agent import AgenteDespesas
from src.agents.licitacoes.agent import AgenteLicitacoes
from src.agents.contratos.agent import AgenteContratos
from src.agents.divida_ativa.agent import AgenteDividaAtiva


RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")


class Orquestrador:
    AGENTES_DISPONIVEIS = (
        "receitas",
        "despesas",
        "licitacoes",
        "contratos",
        )

    def __init__(self):
        chave = os.getenv("GEMINI_API_KEY")

        if not chave:
            raise ValueError(
                "GEMINI_API_KEY não configurada."
            )

        self.modelo = os.getenv(
            "GEMINI_MODEL", "gemini-3.6-flash"
        )

        self.client = genai.Client(api_key=chave)

        # Instancia agentes somente quando necessários.
        self.agentes = {}

    def obter_agente(self, nome):
        if nome not in self.AGENTES_DISPONIVEIS:
            raise ValueError(
                f"Agente desconhecido: {nome}"
            )

        if nome not in self.agentes:
            classes = {
                "receitas": AgenteReceitas,
                "despesas": AgenteDespesas,
                "licitacoes": AgenteLicitacoes,
                "contratos": AgenteContratos,
                "divida_ativa": AgenteDividaAtiva,
            }

            self.agentes[nome] = classes[nome]()

        return self.agentes[nome]

    def identificar_agentes(self, pergunta):
        esquema = {
            "type": "OBJECT",
            "properties": {
                "tarefas": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "agente": {
                                "type": "STRING",
                                "enum": list(
                                    self.AGENTES_DISPONIVEIS
                                ),
                            },
                            "pergunta": {
                                "type": "STRING"
                            },
                        },
                        "required": [
                            "agente", "pergunta"
                        ],
                    },
                }
            },
            "required": ["tarefas"],
        }

        for tentativa in range(3):
            try:
                resposta = self.client.models.generate_content(
                    model=self.modelo,
                    contents=pergunta,
                    config=types.GenerateContentConfig(
                        system_instruction=PROMPT_ROTEAMENTO,
                        response_mime_type="application/json",
                        response_schema=esquema,
                        temperature=0,
                    ),
                )
                break
            except errors.ServerError as erro:
                if erro.code != 503 or tentativa == 2:
                    raise
                espera = 2 ** (tentativa + 1)
                print(
                    f"[AVISO] Gemini indisponível (503). "
                    f"Nova tentativa em {espera}s."
                )
                time.sleep(espera)

        if not resposta.text:
            raise RuntimeError(
                "Roteador não retornou uma decisão."
            )

        decisao = json.loads(resposta.text)
        tarefas = decisao.get("tarefas", [])

        if not isinstance(tarefas, list):
            raise ValueError("Roteamento inválido.")

        selecionados = []
        vistos = set()

        for tarefa in tarefas:
            if not isinstance(tarefa, dict):
                continue

            nome = tarefa.get("agente")
            pergunta_agente = tarefa.get("pergunta")

            if (
                nome in self.AGENTES_DISPONIVEIS
                and isinstance(pergunta_agente, str)
                and pergunta_agente.strip()
                and nome not in vistos
            ):
                selecionados.append({
                    "agente": nome,
                    "pergunta": pergunta_agente.strip(),
                })
                vistos.add(nome)

        return selecionados


    def sintetizar(self, pergunta, respostas):
        contexto = json.dumps(
            {
                "pergunta": pergunta,
                "respostas": respostas,
            },
            ensure_ascii=False,
        )

        resposta = self.client.models.generate_content(
            model=self.modelo,
            contents=contexto,
            config=types.GenerateContentConfig(
                system_instruction=PROMPT_SINTESE,
                temperature=0.1,
            ),
        )

        if not resposta.text:
            raise RuntimeError(
                "Não foi possível sintetizar as respostas."
            )

        return resposta.text

    def executar(self, pergunta):
        if not isinstance(pergunta, str):
            raise ValueError(
                "A pergunta deve ser uma string."
            )

        pergunta = pergunta.strip()

        if not pergunta:
            return {
                "status": "entrada_invalida",
                "agentes_acionados": [],
                "resposta": "Informe uma pergunta.",
            }

        try:
            tarefas = self.identificar_agentes(pergunta)
            selecionados = [
                tarefa["agente"] for tarefa in tarefas
            ]
        
        except Exception as erro:
            print(
                f"[ORQUESTRADOR] Erro no roteamento: "
                f"{type(erro).__name__}: {erro}"
            )
        
            return {
                "status": "erro_roteamento",
                "agentes_acionados": [],
                "resposta": (
                    "Não foi possível identificar "
                    "o agente responsável."
                ),
                "erro_tecnico": str(erro),
            }


        if not selecionados:
            return {
                "status": "fora_escopo",
                "agentes_acionados": [],
                "resposta": (
                    "Não há agente disponível para "
                    "responder a essa pergunta."
                ),
            }

        respostas = {}
        falhas = []

        for tarefa in tarefas:
            nome = tarefa["agente"]
            pergunta_especialista = tarefa["pergunta"]
            
            try:
                agente = self.obter_agente(nome)

                pergunta_isolada = (
                    "Responda exclusivamente à seguinte consulta "
                    "da sua especialidade, sem comentar informações "
                    "de outros agentes ou a comparação geral:\n\n"
                    f"{pergunta_especialista}"
                )
                
                resultado = agente.responder(pergunta_isolada)
                print(f"\n[DEBUG] Agente: {nome}")
                print(f"[DEBUG] Resposta: {resultado!r}")
                
                
                if not isinstance(resultado, str):
                    raise TypeError("Resposta do agente não é texto.")

                mensagens_erro = (
                    "não foi possível processar a consulta",
                    "não foi possível concluir a consulta",
                    "cota temporária da api gemini",
                    "limite temporário de requisições",
                    "resource_exhausted",
                    "quota exceeded",
                    "429 ",
                    "api gemini indisponível",
                    "erro da api gemini",
                )

                if any(
                    mensagem in resultado.lower()
                    for mensagem in mensagens_erro
                ):
                    raise RuntimeError(
                        f"Falha na execução do agente {nome}"
                    )

                if not resultado.strip():
                    raise ValueError(
                        "Resposta vazia do agente."
                    )

                respostas[nome] = resultado

            
            except Exception as erro:
                print(
                    f"\n[ORQUESTRADOR] Falha no agente '{nome}'"
                )
                print("Tipo:", type(erro).__name__)
                print("Mensagem:", str(erro))
            
                falhas.append(nome)


        if not respostas:
            return {
                "status": "erro_execucao",
                "agentes_acionados": selecionados,
                "resposta": (
                    "Os agentes selecionados não "
                    "conseguiram concluir a consulta."
                ),
            }


        if len(respostas) == 1:
            resposta_final = next(
                iter(respostas.values())
            )
        else:
            resposta_final = "\n\n".join(
                f"### {nome.replace('_', ' ').title()}\n{texto}"
                for nome, texto in respostas.items()
            )

            resposta_final += (
                "\n\n**Observação:** Os indicadores "
                "de receitas e despesas podem utilizar "
                "bases e critérios temporais distintos. "
                "Não representam automaticamente um "
                "resultado orçamentário ou fiscal. "
                "Valores inscritos em dívida ativa não equivalem "
                "a receitas arrecadadas ou saldos atualizados."
            )


        if falhas:
            resposta_final += (
                "\n\nConsulta parcial. Não foi possível "
                "obter resposta de: "
                + ", ".join(falhas)
                + "."
            )

        return {
            "status": (
                "parcial" if falhas else "ok"
            ),
            "agentes_acionados": selecionados,
            "resposta": resposta_final,
        }
