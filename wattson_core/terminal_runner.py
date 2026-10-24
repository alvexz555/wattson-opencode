from wattson_core.ai.context import ConversationContext
from wattson_core.ai.conversation import ConversationAI
from wattson_core.ai.engine import AIEngine
from wattson_core.ai import registry
from wattson_core.core.orchestrator import Orchestrator
from wattson_core.diagnostics.adr0 import ADR0DiagnosticTool
from wattson_core.search.contract import SearchTool
from wattson_core.terminal import WattsonTerminal
from wattson_core.update_manager.git import GitUpdateChecker
from wattson_core.update_manager.health import PostUpdateHealthChecker


def create_wattson():
    provider_module = registry.load()

    if provider_module is None:
        raise RuntimeError("Provider configurado indisponível. Verifique WATTSON_PROVIDER.")

    provider = provider_module.WattsonProvider()

    engine = AIEngine(provider)
    context = ConversationContext()
    conversation = ConversationAI(engine, context)

    diagnostic_tool = ADR0DiagnosticTool(".")
    search_tool = SearchTool()
    git_update_checker = GitUpdateChecker(".")
    post_update_health_checker = PostUpdateHealthChecker(".")

    orchestrator = Orchestrator(
        conversation,
        diagnostic_tool=diagnostic_tool,
        search_tool=search_tool,
        git_update_checker=git_update_checker,
        post_update_health_checker=post_update_health_checker,
    )

    return WattsonTerminal(orchestrator)


def run():
    terminal = create_wattson()

    print("WATTSON")
    print("Terminal conectado.")
    print("Digite 'sair' para encerrar.\n")

    while True:
        message = input("Você: ").strip()

        if message.lower() == "sair":
            print("Wattson: Encerrando sessão.")
            break

        if not message:
            continue

        try:
            response = terminal.process(message)
            print(f"Wattson: {response}\n")
        except Exception as error:
            print(f"Wattson: Erro controlado: {error}\n")


if __name__ == "__main__":
    run()
