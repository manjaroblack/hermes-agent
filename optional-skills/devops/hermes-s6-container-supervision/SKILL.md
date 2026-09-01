---
name: hermes-s6-container-supervision
description: Modify or debug s6 services in the Hermes Docker image.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
environments: [s6]
metadata:
  hermes:
    tags: [docker, s6, supervision, gateway, profiles]
    related_skills: [hermes-agent]
---

# Hermes s6-overlay Container Supervision

role: Hermes s6-overlay container maintainer
do: inspect PID1/entrypoint; preserve CMD exit semantics; trace cont-init/profile reconciliation; edit one service source; test signals/restarts/ownership; run Docker harness
inputs: Hermes Docker image, profile/gateway state, s6 service path, entrypoint/CMD args, container logs
outputs: supervised static/profile service, corrected entrypoint/run script, verified boot/restart/exit behavior
¬: supervise main Hermes as a replacement for CMD; swallow exit codes; drop `exec`/signals; run s6 helpers from wrong PATH; chown away required permissions; alter `stage2-hook.sh` without boot test; claim health from PID1 alone

Use this skill when adding/removing a static service, diagnosing a per-profile gateway across `docker restart`, tracing leading-dash CMD arguments, modifying `cont-init.d`, or changing the Phase-4 profile-gateway run script. For ordinary Docker use, see `website/docs/user-guide/docker.md`.

## When to Use

- static service in the Hermes Docker image (for example dashboard)
- per-profile gateway fails to start/restart/survive restart
- container CMD `/opt/hermes/docker/main-wrapper.sh` or leading-dash args
- `cont-init.d` UID remap, volume seed, profile reconciliation
- per-profile gateway run-script or s6 test harness

## Prerequisites

- Linux Docker image with s6-overlay v3.2.3.0 and `environments: [s6]`
- Hermes Dockerfile/entrypoint and profile volume
- Docker available for harness (`tests/docker/` skips when unavailable)
- inspect with `docker exec`, `docker logs`, and absolute `/command/` s6 paths

## Architecture at a Glance

```
/init                                  ← PID 1 (s6-overlay v3.2.3.0)
├── cont-init.d                        ← oneshot setup, runs as root
│   ├── 01-hermes-setup                ← docker/stage2-hook.sh
│   │   ├── UID/GID remap
│   │   ├── chown /opt/data
│   │   ├── chown /opt/data/profiles (every boot)
│   │   ├── seed .env / config.yaml / SOUL.md
│   │   └── skills_sync.py
│   └── 02-reconcile-profiles          ← hermes_cli.container_boot
│       ├── chown /run/service (hermes-writable for runtime register)
│       └── walk $HERMES_HOME/profiles/<name>/gateway_state.json
│           → recreate /run/service/gateway-<name>/
│           → auto-start only those with prior_state == "running"
│
├── s6-rc.d (static services, in /etc/s6-overlay/s6-rc.d/)
│   ├── main-hermes/run                ← exec sleep infinity (no-op slot)
│   └── dashboard/run                  ← if HERMES_DASHBOARD=1, runs `hermes dashboard`
│
├── /run/service (s6-svscan watches; tmpfs)
│   ├── gateway-coder/                 ← runtime-registered per-profile
│   │   ├── type        ("longrun")
│   │   ├── run         ("#!/command/with-contenv sh ... exec s6-setuidgid hermes hermes -p coder gateway run")
│   │   ├── down        (marker — present means "registered but don't auto-start")
│   │   └── log/run     (s6-log → $HERMES_HOME/logs/gateways/coder/current)
│   └── ...
│
└── CMD ("main program")               ← /opt/hermes/docker/main-wrapper.sh
    └── routes user args: bare exec | hermes subcommand | hermes (no args)
        — exec'd by /init with stdin/stdout/stderr inherited (TTY for --tui)
```

## Key Files

| Path | Role |
|---|---|
| `Dockerfile` | s6-overlay install + cont-init.d wiring + `ENTRYPOINT ["/opt/hermes/docker/entrypoint-dispatch.sh"]` |
| `docker/entrypoint-dispatch.sh` | PID-1 dispatcher: exec's `/init` + main-wrapper when the image owns PID 1; on wrapped runtimes (Fly Machines, `docker run --init`) falls back to stage2-hook + main-wrapper directly, restoring the s6 helper PATH first (#38349). |
| `docker/stage2-hook.sh` | The "old entrypoint logic" — UID remap, chown, seed, skills sync. Runs as cont-init.d/01-hermes-setup. |
| `docker/cont-init.d/02-reconcile-profiles` | Calls `hermes_cli.container_boot` on every boot to restore profile gateway slots from the persistent volume. |
| `docker/main-wrapper.sh` | The container's CMD. Routes user args, drops to hermes via `s6-setuidgid`, exec's the chosen program. |
| `docker/s6-rc.d/main-hermes/run` | No-op `sleep infinity` — slot exists so the s6-rc user bundle is valid; main hermes runs as the CMD, not as a supervised service. |
| `docker/s6-rc.d/dashboard/run` | Conditional service — `exec sleep infinity` unless `HERMES_DASHBOARD` is truthy. |
| `docker/entrypoint.sh` | Back-compat shim that `exec`s the stage2 hook. External scripts that hard-coded the old entrypoint path still work. |
| `hermes_cli/service_manager.py` | `S6ServiceManager`: `register_profile_gateway`, `unregister_profile_gateway`, `start/stop/restart/is_running`, `list_profile_gateways`. |
| `hermes_cli/container_boot.py` | `reconcile_profile_gateways()` — walks persistent profiles, regenerates s6 slots, emits `container-boot.log`. |
| `hermes_cli/gateway.py::_dispatch_via_service_manager_if_s6` | Intercepts `hermes gateway start/stop/restart` and routes to s6 when running in a container. |

## Why Architecture B

The v1-v3 plan supervised main Hermes as an s6-rc service, but two s6-overlay v3 constraints make the CMD/main-program pattern load-bearing:

1. `cont-init.d` receives no CMD args, so stage2 cannot parse `docker run <image> chat -q "hi"` into `HERMES_ARGS` for a service run script.
2. `/run/s6/basedir/bin/halt` does **not** propagate the exit code written to `/run/s6-linux-init-container-results/exitcode`; containers exit 143 (SIGTERM). skarnet confirms this in [issue #477](https://github.com/just-containers/s6-overlay/issues/477): _"if you want a container shutdown, you need to either have your CMD exit, or, if you have no CMD, write the container exit code you want then call halt"_.

Therefore `ENTRYPOINT ["/opt/hermes/docker/entrypoint-dispatch.sh"]` under PID1 execs `/init /opt/hermes/docker/main-wrapper.sh "$@"`. `docker run <image> --version` becomes `/init main-wrapper.sh --version`; the wrapper drops to Hermes through `s6-setuidgid` and execs the chosen program, preserving the pre-s6 tini exit contract. If entrypoint is not PID1 (Fly Machines, `docker run --init`), dispatcher skips `/init` (`can only run as pid 1`), restores helper PATH, runs stage2-hook, and execs main-wrapper directly; no supervised services on that path (#38349).

Trade-off: main Hermes remains unsupervised under s6, exactly as under tini; dashboard is the new static guarantee and profile gateways under `/run/service/` are fully supervised.

## Procedure

### 1. Verify PID1 and gateway state

```sh
docker exec <c> sh -c 'cat /proc/1/comm; readlink /proc/1/exe'
# Expect: s6-svscan or init / /package/admin/s6/.../s6-svscan
```

```sh
# /command/ isn't on docker-exec PATH — use absolute path
docker exec <c> /command/s6-svstat /run/service/gateway-<name>
# "up (pid …) … seconds"            → running
# "down (exitcode N) … seconds, normally up, want up, …" → s6 wants it up but the process keeps exiting (crash loop)
# "down … normally up, ready …"     → user stopped it
```

### 2. Control service and read reconciliation log

```sh
docker exec <c> /command/s6-svc -u /run/service/gateway-<name>   # up
docker exec <c> /command/s6-svc -d /run/service/gateway-<name>   # down
docker exec <c> /command/s6-svc -t /run/service/gateway-<name>   # SIGTERM (restart)
```

```sh
docker exec <c> tail -n 50 /opt/data/logs/container-boot.log
# 2026-05-21T06:18:05+0000 profile=coder prior_state=running action=started
# 2026-05-21T06:18:05+0000 profile=writer prior_state=stopped action=registered
```

### 3. Add static service

1. Add `docker/s6-rc.d/<name>/type` with `longrun\n` and `run` using `#!/command/with-contenv sh` + `# shellcheck shell=sh`.
2. Drop to `s6-setuidgid hermes` unless root is required.
3. Add empty `dependencies.d/base`; add empty `user/contents.d/<name>`.
4. Dockerfile `COPY docker/s6-rc.d/` picks it up; no registry edit.

### 4. Change profile gateway run command

Edit `S6ServiceManager._render_run_script` in `hermes_cli/service_manager.py`; `hermes_cli/container_boot.py::_register_service` calls it during reconciliation, so it is the single source of truth. Update `tests/hermes_cli/test_service_manager.py::test_s6_register_creates_service_dir_and_triggers_scan` assertion.

### 5. Run Docker harness

```sh
docker build -t hermes-agent-harness:latest .
HERMES_TEST_IMAGE=hermes-agent-harness:latest scripts/run_tests.sh tests/docker/ -v
# Expect 19 passed, 0 xfailed against the s6 image
```

The harness is under `tests/docker/`; its per-test timeout is 180s (`tests/docker/conftest.py`).

## Pitfalls

- `/command/` is on PATH only for supervision-tree processes; `docker exec <c> s6-svstat` fails. Use `/command/s6-svstat`; `hermes` works through Dockerfile `/opt/hermes/.venv/bin` PATH.
- `02-reconcile-profiles` runs as hermes. Root-owned profiles can block `SOUL.md`; `stage2-hook.sh` chowns `$HERMES_HOME/profiles` to hermes **every boot**, idempotently. Do not remove it.
- `docker exec` defaults root; pass `--user hermes` for profile writes or expect the next boot sweep; in-flight operations can still hit permissions.
- `/run/service` is tmpfs; after restart, wait for reconciliation or inspect `docker logs <c> | grep '02-reconcile'`.
- Gateway `down (exitcode 1)` usually means profile has no model/auth; run `hermes -p <profile> setup`. s6 restart loop is desired until fixed.
- Reconciler uses `SOUL.md` presence as the real-profile marker; missing file is intentional skip. Add even empty `SOUL.md` to opt in.
- `s6-svscanctl -t`/`/run/s6/basedir/bin/halt` produce 143; let CMD/main-wrapper exit for desired code, never control it from finish.

## Verification

- PID1 is `s6-svscan`/s6 init; entrypoint path matches runtime topology
- `s6-svstat` distinguishes running, crash-loop, and user-stopped state
- boot log records `prior_state` and started/registered action
- static service has type/run/dependency/user bundle entries and uses `exec`
- profile gateway survives restart/reconciliation with ownership intact
- Docker harness passes `19 passed, 0 xfailed` when Docker is available
- ordinary CMD exit code is preserved; non-PID1 fallback does not invoke `/init`

## Related Skills

- `hermes-agent-dev`: Hermes codebase navigation
- `hermes-tool-quirks`: Hermes-tool workarounds when debugging s6 interactions
