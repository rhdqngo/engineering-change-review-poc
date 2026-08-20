from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

import uvicorn

from .data import validate_all
from .evaluation import evaluate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ecr-poc",
        description="Evidence-grounded NASA cFS engineering change review PoC",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("validate-data", help="verify frozen cases and NASA source hashes")
    evaluation = subcommands.add_parser("evaluate", help="run all pre-registered cases")
    evaluation.add_argument("--provider", choices=["fixture", "vertex-adk"], required=True)
    evaluation.add_argument("--embedding", choices=["local", "vertex"], required=True)
    evaluation.add_argument("--output", type=Path)
    evaluation.add_argument("--inject-unsupported", action="store_true")
    serve = subcommands.add_parser("serve", help="run the Demo UI/API")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "validate-data":
        print(json.dumps(validate_all(), indent=2))
        return
    if args.command == "evaluate":
        run = asyncio.run(
            evaluate(
                provider_name=args.provider,
                embedding_provider=args.embedding,
                output_path=args.output,
                inject_unsupported=args.inject_unsupported,
            )
        )
        print(json.dumps(run.metrics, indent=2))
        return
    if args.command == "serve":
        uvicorn.run("ecr_poc.web:app", host=args.host, port=args.port)
