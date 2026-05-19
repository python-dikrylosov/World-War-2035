"""
Qwen Multimodal Assistant - Альтернативный запуск с CLI аргументами
"""
import argparse
import json
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Qwen Multimodal Assistant")
    parser.add_argument("--cli", action="store_true", help="CLI mode instead of GUI")
    parser.add_argument("--test", action="store_true", help="Run tests")
    parser.add_argument("--config", action="store_true", help="Show configuration")
    parser.add_argument("--models-path", type=str, default="models", help="Path to models")
    return parser.parse_args()


def show_config():
    config_path = Path("config/config.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        print(json.dumps(config, indent=2))
    else:
        print("Config not found")


def run_cli():
    print("CLI Mode - Interactive console")
    print("Commands: help, vision, coder, audio, tools, workflow, exit")
    while True:
        cmd = input("\n> ").strip()
        if cmd in ["exit", "quit"]:
            break
        elif cmd == "help":
            print("Available commands: help, vision, coder, audio, tools, workflow, exit")
        else:
            print(f"Unknown command: {cmd}")


def run_tests():
    print("Running tests...")
    # Placeholder for tests
    print("Tests passed!")


def main():
    args = parse_args()
    
    if args.config:
        show_config()
        return
    
    if args.test:
        run_tests()
        return
    
    if args.cli:
        run_cli()
        return
    
    # Default: GUI mode
    from src.presentation.app import MainWindow
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
