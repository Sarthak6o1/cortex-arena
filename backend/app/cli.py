import argparse
import asyncio

from backend.app.config import get_settings
from backend.app.setup import RECOMMENDED_OLLAMA_MODELS, get_setup_status, pull_recommended_model


def main() -> None:
    asyncio.run(async_main())


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="Cortex Arena setup helper")
    parser.add_argument(
        "--pull-recommended",
        action="store_true",
        help="Pull all missing recommended Ollama models.",
    )
    args = parser.parse_args()

    settings = get_settings()
    status = await get_setup_status(settings)

    print(f"Ollama running: {status.ollama_running}")
    print("Installed models:")
    for model in status.installed_models:
        print(f"  - {model.id} {model.size or ''}".rstrip())

    print("Recommended free models:")
    for model in status.recommended_models:
        marker = "installed" if model.installed else "missing"
        print(f"  - {model.id} ({model.size}) [{marker}]")

    if args.pull_recommended:
        if not status.ollama_running:
            raise SystemExit("Start Ollama before pulling models.")
        for model in RECOMMENDED_OLLAMA_MODELS:
            if model.id in {installed.id for installed in status.installed_models}:
                continue
            print(f"Pulling {model.id}...")
            messages = await pull_recommended_model(settings, model.id)
            if messages:
                print(f"  {messages[-1]}")


if __name__ == "__main__":
    main()
