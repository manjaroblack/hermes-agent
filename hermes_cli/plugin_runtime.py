"""Context-local identity for plugin callback reads."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

_CURRENT_PLUGIN_SESSION: ContextVar[Optional[str]] = ContextVar(
    "current_plugin_session", default=None
)


@contextmanager
def plugin_callback_scope(session_id: object) -> Iterator[None]:
    token = _CURRENT_PLUGIN_SESSION.set(str(session_id).strip() if session_id else None)
    try:
        yield
    finally:
        _CURRENT_PLUGIN_SESSION.reset(token)


def current_plugin_session() -> Optional[str]:
    return _CURRENT_PLUGIN_SESSION.get()
