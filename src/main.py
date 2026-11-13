from src.agents.orchestrador import Orquestrador


def main():
    orquestrador = Orquestrador()

    print("=" * 60)
    print("AGENTE DE FINANÇAS PÚBLICAS — PALMAS/TO")
    print("=" * 60)
    print("Digite 'sair' para encerrar.\n")

    while True:
        try:
            pergunta = input("Pergunta: ").strip()

            if pergunta.lower() in ("sair", "exit", "quit"):
                print("\nEncerrando o sistema.")
                break

            if not pergunta:
                continue

            resultado = orquestrador.executar(pergunta)

            print("\n" + "=" * 60)
            print("RESPOSTA")
            print("=" * 60)
            print(resultado["resposta"])

            print(
                "\nAgentes acionados:",
                ", ".join(resultado["agentes_acionados"])
                or "Nenhum"
            )

            print("Status:", resultado["status"])
            print("=" * 60 + "\n")

        except KeyboardInterrupt:
            print("\nExecução interrompida.")
            break

        except Exception as erro:
            print(
                f"\nErro: {type(erro).__name__}: {erro}\n"
            )


if __name__ == "__main__":
    main()
