"""CLI entry point."""

import asyncio
import sys

from config import get_settings
from core.logging import setup_logging
from gateway.server import run_server


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="AI Agent CLI")
    parser.add_argument("command", choices=["start", "init", "doctor"])
    parser.add_argument("--port", type=int, help="Port to run server on")
    parser.add_argument("--host", type=str, default="localhost", help="Host address")

    args = parser.parse_args()

    settings = get_settings()
    setup_logging(level=settings.logging.level, format_type=settings.logging.format)

    if args.command == "start":
        print(f"Starting AI Agent server on {args.host}:{args.port or settings.gateway.web.port}")
        run_server()

    elif args.command == "init":
        print("Initializing AI Agent workspace...")
        asyncio.run(_init_workspace())

    elif args.command == "doctor":
        print("Running diagnostics...")
        asyncio.run(_run_doctor())


async def _init_workspace():
    """Initialize workspace directories."""
    from pathlib import Path
    from config import get_settings

    settings = get_settings()

    # Create workspace directory
    workspace = Path(settings.memory.file_store.path).expanduser()
    workspace.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (workspace / "memory").mkdir(exist_ok=True)
    (workspace / "memory" / "sessions").mkdir(exist_ok=True)
    (workspace / "users").mkdir(exist_ok=True)

    print(f"Workspace initialized at: {workspace}")


async def _run_doctor():
    """Run system diagnostics."""
    from config import get_settings
    from core.model.router import ModelRouter

    settings = get_settings()

    print("\n=== AI Agent Diagnostics ===\n")

    # Check configuration
    print(f"[1] Configuration")
    print(f"    Deploy mode: {settings.deploy_mode}")
    print(f"    Primary model: {settings.model.primary}")
    print(f"    Version: {settings.version}")

    # Check API keys
    print(f"\n[2] API Keys")
    for model_name in ["deepseek", "zhipu", "qwen", "openai"]:
        key = settings.get_model_api_key(model_name)
        status = "✓ configured" if key else "✗ not set"
        print(f"    {model_name}: {status}")

    # Check model router
    print(f"\n[3] Model Router")
    router = ModelRouter()
    health = await router.health_check()
    print(f"    Status: {health['status']}")
    print(f"    Models available: {', '.join(health['configured_models'])}")

    print("\n=== All checks completed ===\n")


if __name__ == "__main__":
    main()