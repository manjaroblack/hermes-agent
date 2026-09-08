from __future__ import annotations

import builtins
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import quote

import aiohttp
import pytest

from gateway.config import PlatformConfig
import plugins.platforms.discord.adapter as discord_adapter_module
from plugins.platforms.discord.adapter import DiscordAdapter


class CapturedFile:
    created: list["CapturedFile"] = []

    def __init__(self, fp, filename=None, **kwargs):
        self.fp = fp
        self.filename = filename
        self.kwargs = kwargs
        if isinstance(fp, (str, Path)):
            self.content = Path(fp).read_bytes()
        else:
            self.content = fp.getvalue()
        type(self).created.append(self)


class FakeRoute:
    def __init__(self, method, path, **kwargs):
        self.method = method
        self.path = path
        self.kwargs = kwargs


def _message(message_id: str, *, attachments: bool = True):
    return SimpleNamespace(
        id=message_id,
        attachments=[SimpleNamespace(filename="uploaded.bin")] if attachments else [],
    )


def _channel(channel_id: int, *, attachments: bool = True):
    channel = SimpleNamespace(id=channel_id)
    channel.send = AsyncMock(return_value=_message(f"message-{channel_id}", attachments=attachments))
    return channel


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    CapturedFile.created.clear()
    return DiscordAdapter(PlatformConfig(enabled=True, token="test-token"))


def _install_client(adapter, parent, thread, *, cache_hit=True):
    get_calls = []

    def get_channel(channel_id):
        get_calls.append(channel_id)
        if channel_id == thread.id:
            return thread if cache_hit else None
        if channel_id == parent.id:
            return parent
        return None

    async def fetch_channel(channel_id):
        if channel_id == thread.id:
            return thread
        if channel_id == parent.id:
            return parent
        return None

    adapter._client = SimpleNamespace(
        get_channel=MagicMock(side_effect=get_channel),
        fetch_channel=AsyncMock(side_effect=fetch_channel),
    )
    return get_calls


def test_resolve_send_target_id_preserves_truthy_thread_semantics():
    cases = (
        ("100", None, "100"),
        ("100", {}, "100"),
        ("100", {"thread_id": None}, "100"),
        ("100", {"thread_id": ""}, "100"),
        ("100", {"thread_id": 200}, "200"),
        ("100", {"thread_id": "200"}, "200"),
    )
    for chat_id, metadata, expected in cases:
        original = None if metadata is None else dict(metadata)
        assert DiscordAdapter._resolve_send_target_id(chat_id, metadata) == expected
        assert metadata == original


@pytest.mark.asyncio
@pytest.mark.parametrize("cache_hit", [True, False])
async def test_send_text_uses_thread_target_and_history_key(adapter, cache_hit):
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread, cache_hit=cache_hit)

    result = await adapter.send(
        "100",
        "thread text",
        metadata={"thread_id": "200"},
    )

    assert result.success is True
    assert get_calls == [200]
    if cache_hit:
        adapter._client.fetch_channel.assert_not_awaited()
    else:
        adapter._client.fetch_channel.assert_awaited_once_with(200)
    parent.send.assert_not_awaited()
    thread.send.assert_awaited_once()
    assert adapter._last_self_message_id["200"] == "message-200"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "path_argument", "filename"),
    [
        ("send_document", "file_path", "report.txt"),
        ("send_image_file", "image_path", "picture.png"),
        ("send_video", "video_path", "clip.mp4"),
    ],
)
@pytest.mark.parametrize("cache_hit", [True, False])
async def test_local_media_methods_upload_to_thread(
    adapter, tmp_path, monkeypatch, method_name, path_argument, filename, cache_hit
):
    media_path = tmp_path / filename
    media_path.write_bytes(b"real temporary media bytes")
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread, cache_hit=cache_hit)
    monkeypatch.setattr(discord_adapter_module.discord, "File", CapturedFile)

    kwargs = {
        "chat_id": "100",
        path_argument: str(media_path),
        "caption": "caption",
        "metadata": {"thread_id": "200"},
    }
    if method_name == "send_document":
        kwargs["file_name"] = "renamed.txt"

    result = await getattr(adapter, method_name)(**kwargs)

    assert result.success is True
    assert get_calls == [200]
    if not cache_hit:
        adapter._client.fetch_channel.assert_awaited_once_with(200)
    parent.send.assert_not_awaited()
    thread.send.assert_awaited_once()
    sent_file = thread.send.call_args.kwargs["files"][0]
    assert sent_file.content == b"real temporary media bytes"
    assert sent_file.filename == ("renamed.txt" if method_name == "send_document" else filename)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "url", "content_type", "filename"),
    [
        ("send_image", "https://example.test/image.png", "image/png", "image.png"),
        ("send_animation", "https://example.test/animation.gif", "image/gif", "animation.gif"),
    ],
)
async def test_downloaded_image_media_uses_thread_target(
    adapter, monkeypatch, method_name, url, content_type, filename
):
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread)
    monkeypatch.setattr(discord_adapter_module, "is_safe_url", lambda value: True)
    monkeypatch.setattr(discord_adapter_module.discord, "File", CapturedFile)

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    async def read_image(*args, **kwargs):
        return 200, b"deterministic image bytes", {"content-type": content_type}

    monkeypatch.setattr(aiohttp, "ClientSession", lambda **kwargs: Session())
    monkeypatch.setattr(discord_adapter_module, "_read_url_image_with_redirect_guard", read_image)

    result = await getattr(adapter, method_name)(
        "100",
        url,
        caption="media caption",
        metadata={"thread_id": "200"},
    )

    assert result.success is True
    assert get_calls == [200]
    parent.send.assert_not_awaited()
    thread.send.assert_awaited_once()
    sent_file = thread.send.call_args.kwargs["file"]
    assert sent_file.content == b"deterministic image bytes"
    assert sent_file.filename == filename


@pytest.mark.asyncio
async def test_image_download_failure_text_fallback_preserves_thread_metadata(
    adapter, monkeypatch
):
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread)
    monkeypatch.setattr(discord_adapter_module, "is_safe_url", lambda value: True)
    metadata = {"thread_id": "200"}

    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    async def read_image(*args, **kwargs):
        raise RuntimeError("deterministic download failure")

    monkeypatch.setattr(aiohttp, "ClientSession", lambda **kwargs: Session())
    monkeypatch.setattr(discord_adapter_module, "_read_url_image_with_redirect_guard", read_image)

    result = await adapter.send_image(
        "100",
        "https://example.test/fallback.png",
        caption="fallback caption",
        metadata=metadata,
    )

    assert result.success is True
    assert get_calls == [200, 200]
    parent.send.assert_not_awaited()
    thread.send.assert_awaited_once()
    assert "https://example.test/fallback.png" in thread.send.call_args.kwargs["content"]
    assert metadata == {"thread_id": "200"}


@pytest.mark.asyncio
async def test_image_import_error_text_fallback_preserves_thread_metadata(
    adapter, monkeypatch
):
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread)
    monkeypatch.setattr(discord_adapter_module, "is_safe_url", lambda value: True)
    real_import = builtins.__import__

    def fail_aiohttp_import(name, *args, **kwargs):
        if name == "aiohttp":
            raise ImportError("deterministic missing aiohttp")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_aiohttp_import)
    result = await adapter.send_image(
        "100",
        "https://example.test/import-fallback.png",
        metadata={"thread_id": "200"},
    )

    assert result.success is True
    assert get_calls == [200]
    parent.send.assert_not_awaited()
    thread.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_multiple_local_images_target_thread_and_keep_batching(
    adapter, tmp_path, monkeypatch
):
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread)
    monkeypatch.setattr(discord_adapter_module.discord, "File", CapturedFile)
    image_paths = []
    for index in range(11):
        path = tmp_path / f"image-{index}.png"
        path.write_bytes(f"image-{index}".encode())
        image_paths.append(path)

    await adapter.send_multiple_images(
        "100",
        [(f"file://{quote(str(path))}", f"alt-{index}") for index, path in enumerate(image_paths)],
        metadata={"thread_id": "200"},
        human_delay=0.0,
    )

    assert get_calls == [200]
    parent.send.assert_not_awaited()
    assert thread.send.await_count == 2
    assert [len(call.kwargs["files"]) for call in thread.send.await_args_list] == [10, 1]


@pytest.mark.asyncio
async def test_multiple_images_fallback_remains_thread_targeted(
    adapter, tmp_path, monkeypatch
):
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread)
    monkeypatch.setattr(discord_adapter_module.discord, "File", CapturedFile)
    image_path = tmp_path / "fallback.png"
    image_path.write_bytes(b"fallback image")
    thread.send = AsyncMock(
        side_effect=[RuntimeError("batch failure"), _message("fallback-message")]
    )

    await adapter.send_multiple_images(
        "100",
        [(f"file://{quote(str(image_path))}", "fallback")],
        metadata={"thread_id": "200"},
    )

    assert get_calls == [200, 200]
    parent.send.assert_not_awaited()
    assert thread.send.await_count == 2
    assert all(call.kwargs.get("files") for call in thread.send.await_args_list)


@pytest.mark.asyncio
async def test_voice_native_http_and_file_fallback_use_selected_thread(
    adapter, tmp_path, monkeypatch
):
    audio_path = tmp_path / "voice.ogg"
    audio_path.write_bytes(b"voice bytes")
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread)
    monkeypatch.setattr(discord_adapter_module.discord, "File", CapturedFile)
    monkeypatch.setattr(discord_adapter_module.discord.http, "Route", FakeRoute)

    request = AsyncMock(return_value={"id": "native-voice"})
    adapter._client.http = SimpleNamespace(request=request)
    result = await adapter.send_voice(
        "100", str(audio_path), metadata={"thread_id": "200"}
    )

    assert result.success is True
    assert result.message_id == "native-voice"
    route = request.await_args.args[0]
    assert route.kwargs["channel_id"] == 200
    assert get_calls == [200]
    parent.send.assert_not_awaited()
    thread.send.assert_not_awaited()

    request.reset_mock(side_effect=True, return_value=True)
    request.side_effect = RuntimeError("native voice unsupported")
    thread.send.reset_mock()
    result = await adapter.send_voice(
        "100", str(audio_path), metadata={"thread_id": "200"}
    )

    assert result.success is True
    assert get_calls == [200, 200]
    parent.send.assert_not_awaited()
    thread.send.assert_awaited_once()
    assert thread.send.call_args.kwargs["file"].content == b"voice bytes"


@pytest.mark.asyncio
async def test_explicit_missing_thread_never_falls_back_to_parent(adapter, tmp_path):
    media_path = tmp_path / "missing-thread.txt"
    media_path.write_bytes(b"content")
    get_calls = []

    def get_channel(channel_id):
        get_calls.append(channel_id)
        return None

    adapter._client = SimpleNamespace(
        get_channel=MagicMock(side_effect=get_channel),
        fetch_channel=AsyncMock(return_value=None),
    )

    result = await adapter.send_document(
        "100", str(media_path), metadata={"thread_id": "200"}
    )

    assert result.success is False
    assert result.error == "Channel 200 not found"
    assert get_calls == [200]
    adapter._client.fetch_channel.assert_awaited_once_with(200)


@pytest.mark.asyncio
@pytest.mark.parametrize("metadata", [None, {}, {"thread_id": None}, {"thread_id": ""}])
async def test_empty_thread_metadata_keeps_parent_media_target(adapter, tmp_path, metadata):
    media_path = tmp_path / "parent.txt"
    media_path.write_bytes(b"parent content")
    parent = _channel(100)
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread)
    result = await adapter.send_document("100", str(media_path), metadata=metadata)

    assert result.success is True
    assert get_calls == [100]
    parent.send.assert_awaited_once()
    thread.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_forum_parent_behavior_stays_unchanged_without_thread_metadata(
    adapter, tmp_path, monkeypatch
):
    media_path = tmp_path / "forum.txt"
    media_path.write_bytes(b"forum content")
    parent = _channel(100)
    parent.type = 15
    forum_thread_channel = _channel(300)
    forum_thread = SimpleNamespace(
        id=300,
        message=_message("starter", attachments=True),
        thread=forum_thread_channel,
    )
    parent.create_thread = AsyncMock(return_value=forum_thread)
    thread = _channel(200)
    _install_client(adapter, parent, thread)
    monkeypatch.setattr(discord_adapter_module.discord, "File", CapturedFile)

    result = await adapter.send_document("100", str(media_path))

    assert result.success is True
    parent.create_thread.assert_awaited_once()
    parent.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_forum_thread_metadata_sends_directly_to_thread(
    adapter, tmp_path, monkeypatch
):
    media_path = tmp_path / "forum-thread.txt"
    media_path.write_bytes(b"forum thread content")
    parent = _channel(100)
    parent.type = 15
    parent.create_thread = AsyncMock()
    thread = _channel(200)
    get_calls = _install_client(adapter, parent, thread)
    monkeypatch.setattr(discord_adapter_module.discord, "File", CapturedFile)

    result = await adapter.send_document(
        "100", str(media_path), metadata={"thread_id": "200"}
    )

    assert result.success is True
    assert get_calls == [200]
    parent.create_thread.assert_not_awaited()
    parent.send.assert_not_awaited()
    thread.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_reports_thread_not_found_without_parent_retry(adapter):
    get_calls = []

    def get_channel(channel_id):
        get_calls.append(channel_id)
        return None

    adapter._client = SimpleNamespace(
        get_channel=MagicMock(side_effect=get_channel),
        fetch_channel=AsyncMock(return_value=None),
    )

    result = await adapter.send("100", "text", metadata={"thread_id": "200"})

    assert result.success is False
    assert result.error == "Thread 200 not found"
    assert get_calls == [200]
    adapter._client.fetch_channel.assert_awaited_once_with(200)
