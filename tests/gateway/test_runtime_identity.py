from __future__ import annotations

from gateway.status import build_runtime_identity_snapshot


def test_runtime_identity_snapshot_contains_bounded_live_import_identity():
    snapshot = build_runtime_identity_snapshot(pid=None)
    assert snapshot["pid"] > 0
    assert snapshot["service_interpreter"]
    assert snapshot["python_version"]
    assert snapshot["sqlite_version"]
    assert set(snapshot["module_origins"]) >= {"hermes_constants", "hermes_cli", "gateway"}
    assert all("token" not in key.casefold() for key in snapshot)
    assert all("password" not in key.casefold() for key in snapshot)
    assert all("secret" not in key.casefold() for key in snapshot)
