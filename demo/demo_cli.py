#!/usr/bin/env python3
"""AnonyMCP interactive demo — shows all core capabilities.

Run this script to see AnonyMCP detect, classify, and anonymize PII
in real-time. Designed to be screen-recorded for README GIF / YouTube.

Usage:
    cd ~/Desktop/anonymcp
    uv run python demo/demo_cli.py
"""

from __future__ import annotations

import json
import sys
import time

# Rich for pretty terminal output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
except ImportError:
    print("Installing rich for demo display...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "--quiet"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box

import logging
import structlog

# Suppress structlog output for clean demo display
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.CRITICAL),
)

from anonymcp.config.settings import AnonyMCPSettings
from anonymcp.engine.detector import TextDetector
from anonymcp.engine.anonymizer import TextAnonymizer
from anonymcp.engine.classifier import TextClassifier
from anonymcp.policy.engine import PolicyEngine
from anonymcp.policy.models import GovernancePolicy

console = Console(width=90)

# ---------------------------------------------------------------------------
# Demo Scenarios
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "title": "Customer Support Email",
        "description": "A typical support ticket containing multiple PII types",
        "text": (
            "Hi, my name is Sarah Johnson and I need help with my account. "
            "My email is sarah.johnson@acmecorp.com and my phone number is "
            "(555) 867-5309. The last four digits of my credit card are 4242 "
            "and my full card number is 4111-1111-1111-1111. "
            "My SSN is 123-45-6789. Please help me reset my password."
        ),
    },
    {
        "title": "Medical Record Note",
        "description": "A clinical note with protected health information",
        "text": (
            "Patient: Michael Chen, DOB: 03/15/1985. "
            "Medical license #ML-2847591. "
            "Patient presented with symptoms on 2026-02-28 at "
            "123 Oak Street, Springfield, IL. "
            "Contact: mchen@hospital.org, phone 555-234-5678. "
            "Insurance ID: BCBS-9876543210."
        ),
    },
    {
        "title": "Clean Business Text",
        "description": "A paragraph with no PII — should classify as PUBLIC",
        "text": (
            "Our Q1 2026 revenue grew 15% year-over-year, driven by strong "
            "demand in the enterprise segment. The product team shipped 3 major "
            "features and reduced p99 latency by 40%. We expect continued "
            "momentum heading into Q2."
        ),
    },
]


def pause(seconds: float = 1.5) -> None:
    time.sleep(seconds)


def run_demo() -> None:
    # Init
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]AnonyMCP[/] — Data Governance for AI Workflows\n"
            "[dim]PII Detection • Classification • Anonymization • Audit[/]",
            border_style="cyan",
            padding=(1, 4),
        )
    )
    pause(1)

    console.print("\n[bold]Initializing governance engine...[/]")
    policy = GovernancePolicy()
    policy_engine = PolicyEngine(policy=policy)
    detector = TextDetector()
    anonymizer = TextAnonymizer(policy=policy)
    classifier = TextClassifier(policy_engine=policy_engine)
    console.print("[green]✓[/] Presidio Analyzer loaded")
    console.print("[green]✓[/] Policy engine ready (default policy v1.0)")
    console.print("[green]✓[/] Anonymizer configured")
    pause(1)

    for i, scenario in enumerate(SCENARIOS, 1):
        console.print()
        console.rule(f"[bold yellow]Demo {i}/{len(SCENARIOS)}: {scenario['title']}[/]")
        console.print(f"[dim]{scenario['description']}[/]\n")
        pause(0.5)

        # Show input text
        console.print(Panel(scenario["text"], title="[bold]Input Text[/]", border_style="white"))
        pause(1)

        # Step 1: Detect
        console.print("\n[bold cyan]Step 1:[/] Detecting PII entities...")
        start = time.monotonic()
        detection = detector.detect(scenario["text"], score_threshold=0.4)
        duration = (time.monotonic() - start) * 1000
        pause(0.5)

        if detection.entities_found == 0:
            console.print(f"  [green]No PII detected[/] ({duration:.0f}ms)")
        else:
            table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
            table.add_column("Entity Type", style="yellow")
            table.add_column("Value", style="red")
            table.add_column("Score", justify="right")
            for r in detection.results:
                table.add_row(
                    r["entity_type"],
                    r["text"][:30] + ("..." if len(r["text"]) > 30 else ""),
                    f"{r['score']:.0%}",
                )
            console.print(table)
            console.print(f"  [dim]Found {detection.entities_found} entities in {duration:.0f}ms[/]")
        pause(1)

        # Step 2: Classify
        console.print("\n[bold cyan]Step 2:[/] Classifying sensitivity...")
        entity_types = detection.entity_types()
        scores = [r["score"] for r in detection.results]
        cls_result = classifier.classify(entity_types, scores=scores)
        pause(0.5)

        level = cls_result.classification.value
        color_map = {
            "PUBLIC": "green",
            "INTERNAL": "blue",
            "CONFIDENTIAL": "yellow",
            "RESTRICTED": "red",
        }
        color = color_map.get(level, "white")
        console.print(f"  Classification: [bold {color}]{level}[/]")
        console.print(f"  Reason: [dim]{cls_result.reason}[/]")
        pause(1)

        # Step 3: Anonymize (only if PII found)
        if detection.entities_found > 0:
            console.print("\n[bold cyan]Step 3:[/] Anonymizing PII...")
            anon_result = anonymizer.anonymize(scenario["text"], detection.raw_results)
            pause(0.5)

            console.print(
                Panel(
                    anon_result.anonymized_text,
                    title="[bold green]Protected Output[/]",
                    border_style="green",
                )
            )
            console.print(f"  [dim]{anon_result.entities_anonymized} entities anonymized[/]")

            # Show operators used
            if anon_result.operators_applied:
                ops = ", ".join(
                    f"{k}→{v}" for k, v in anon_result.operators_applied.items()
                )
                console.print(f"  [dim]Operators: {ops}[/]")
        else:
            console.print("\n[bold cyan]Step 3:[/] [green]No anonymization needed — text is clean[/]")

        pause(2)

    # Summary
    console.print()
    console.rule("[bold cyan]Demo Complete[/]")
    console.print()
    console.print(
        Panel.fit(
            "[bold]AnonyMCP[/] plugs into any MCP-compatible AI workflow:\n\n"
            "  • [cyan]Pre-LLM screening[/]  — sanitize input before it hits the model\n"
            "  • [cyan]Post-LLM filtering[/] — catch PII leaking in model responses\n"
            "  • [cyan]RAG governance[/]     — classify retrieved docs by sensitivity\n"
            "  • [cyan]Compliance audit[/]   — full trail of every governance action\n\n"
            "[dim]GitHub: https://github.com/frankkyazze9/anonymcp[/]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()


if __name__ == "__main__":
    run_demo()
