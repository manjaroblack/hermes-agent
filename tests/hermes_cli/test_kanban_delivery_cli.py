"""CLI contract tests for bounded delivery-controller entrypoints."""

from __future__ import annotations

import argparse

from hermes_cli import kanban


def test_delivery_controller_parser_requires_explicit_single_step_mode() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="kanban_action")
    kanban.build_parser(subparsers)

    args = parser.parse_args(
        ["kanban", "delivery", "controller", "--task", "task-123", "--once", "--json"]
    )

    assert args.kanban_action == "delivery"
    assert args.delivery_action == "controller"
    assert args.task_id == "task-123"
    assert args.once is True
    assert args.json is True


def test_delivery_controller_dispatch_refuses_unbounded_mode(capsys) -> None:
    args = argparse.Namespace(
        delivery_action="controller",
        task_id="task-123",
        once=False,
        json=True,
    )

    assert kanban._dispatch_delivery(args) == 2
    assert "requires --once" in capsys.readouterr().err


def test_delivery_health_parser_accepts_durable_evidence_path() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="kanban_action")
    kanban.build_parser(subparsers)

    args = parser.parse_args(
        ["kanban", "delivery", "record-health", "task-123", "--evidence", "/tmp/health.json"]
    )

    assert args.delivery_action == "record-health"
    assert args.task_id == "task-123"
    assert args.evidence == "/tmp/health.json"
