from __future__ import annotations

import asyncio
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import Platform, PlatformConfig
from gateway.run import GatewayRunner
from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
from hermes_cli import kanban_db_notify as kbn
import plugins.platforms.discord.adapter as discord_adapter_module
from plugins.platforms.discord.adapter import DiscordAdapter


class CapturedFile:
    def __init__(self, fp, filename=None, **kwargs):
        self.fp = fp
        self.filename = filename
        self.content = Path(fp).read_bytes() if isinstance(fp, (str, Path)) else fp.getvalue()
        self.kwargs = kwargs


def _message(message_id: str):
    return SimpleNamespace(
        id=message_id,
        attachments=[SimpleNamespace(filename="artifact.txt")],
    )


@pytest.fixture
def isolated_kanban(tmp_path, monkeypatch):
    for name in list(os.environ):
        if name.startswith("HERMES_KANBAN_"):
            monkeypatch.delenv(name, raising=False)
    hermes_home = tmp_path / "hermes"
    kanban_home = tmp_path / "private-kanban-home"
    hermes_home.mkdir()
    kanban_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("HERMES_KANBAN_HOME", str(kanban_home))

    initialized_paths = getattr(kb, "_INITIALIZED_PATHS", None)
    if initialized_paths is not None:
        initialized_paths.clear()
    db_path = kb.kanban_db_path()
    assert db_path.is_relative_to(kanban_home.resolve())
    kb.init_db()
    return db_path


def _make_runner(adapter):
    runner = GatewayRunner.__new__(GatewayRunner)
    runner._running = True
    runner.adapters = {Platform.DISCORD: adapter}
    runner._kanban_sub_fail_counts = {}
    runner._kanban_dispatcher_lock_handle = object()
    runner._active_profile_name = lambda: "default"
    return runner


async def _run_one_notifier_tick(monkeypatch, runner):
    real_sleep = asyncio.sleep

    async def fake_sleep(delay):
        if delay == 5:
            return None
        runner._running = False
        await real_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    await runner._kanban_notifier_watcher(interval=1)


@pytest.mark.asyncio
async def test_completed_artifact_notification_keeps_text_and_file_in_thread(
    isolated_kanban, tmp_path, monkeypatch
):
    artifact = tmp_path / "completion.txt"
    artifact.write_bytes(b"completion artifact bytes")
    parent_id = "100"
    thread_id = "200"
    parent = SimpleNamespace(id=int(parent_id), send=AsyncMock())
    thread = SimpleNamespace(id=int(thread_id), send=AsyncMock(return_value=_message("thread-message")))
    get_calls = []

    def get_channel(channel_id):
        get_calls.append(channel_id)
        return thread if channel_id == int(thread_id) else None

    adapter = DiscordAdapter(PlatformConfig(enabled=True, token="test-token"))
    adapter._client = SimpleNamespace(
        get_channel=MagicMock(side_effect=get_channel),
        fetch_channel=AsyncMock(side_effect=lambda channel_id: thread if channel_id == int(thread_id) else None),
    )
    monkeypatch.setattr(discord_adapter_module.discord, "File", CapturedFile)

    conn = kbc.connect()
    try:
        task_id = kb.create_task(conn, title="artifact notification", assignee="worker")
        kbn.add_notify_sub(
            conn,
            task_id=task_id,
            platform=Platform.DISCORD.value,
            chat_id=parent_id,
            thread_id=thread_id,
            delivery_mode="notify",
        )
        assert kb.complete_task(
            conn,
            task_id,
            summary="completed with artifact",
            metadata={"artifacts": [str(artifact)]},
        )
    finally:
        conn.close()

    runner = _make_runner(adapter)
    await _run_one_notifier_tick(monkeypatch, runner)

    assert get_calls
    assert set(get_calls) == {int(thread_id)}
    parent.send.assert_not_awaited()
    assert thread.send.await_count == 2
    text_call, file_call = thread.send.await_args_list
    assert text_call.kwargs["content"]
    assert "files" not in text_call.kwargs
    uploaded = file_call.kwargs["files"]
    assert len(uploaded) == 1
    assert uploaded[0].content == b"completion artifact bytes"
    assert uploaded[0].filename == "completion.txt"
