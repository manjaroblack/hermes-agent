---
name: docker-management
description: Manage Docker containers, images, volumes, and Compose.
version: 1.0.0
author: sprmn24
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [docker, containers, devops, infrastructure, compose, images, volumes, networks, debugging]
    category: devops
    requires_toolsets: [terminal]
---

# Docker Management

role: Docker/Compose operations operator
do: classify request; inspect before destructive action; manage containers/images/volumes/networks; debug logs/resources; validate Compose; verify state/ports/disk; optimize Dockerfile
inputs: Docker/Compose project, container/image/volume/network name, ports/env/limits, cleanup target
outputs: running/stopped/inspected resources, Compose stack, diagnostics, verified disk/port/health state
¬: destroy volumes without confirmation; expose passwords; prune broadly before diagnosis; assume service healthy from `docker ps`; bind app only to localhost in container; use unpinned `latest`; run privileged/root unnecessarily

Manage Docker containers, images, volumes, networks, and Compose with the standard Docker CLI. No dependency beyond Docker.

## When to Use

- container lifecycle, shell/logs/inspect/stats/debugging
- image build/pull/push/tag/cleanup
- Compose multi-service stacks
- volume/network management
- Docker disk usage/cleanup or Dockerfile review

## Prerequisites

- Docker Engine installed/running
- user in `docker` group or permission to use `sudo`
- Docker Compose v2

```bash
docker --version && docker compose version
```

## Quick Reference

| Task | Command |
|------|---------|
| Run container (background) | `docker run -d --name NAME IMAGE` |
| Stop + remove | `docker stop NAME && docker rm NAME` |
| View logs (follow) | `docker logs --tail 50 -f NAME` |
| Shell into container | `docker exec -it NAME /bin/sh` |
| List all containers | `docker ps -a` |
| Build image | `docker build -t TAG .` |
| Compose up | `docker compose up -d` |
| Compose down | `docker compose down` |
| Disk usage | `docker system df` |
| Cleanup dangling | `docker image prune && docker container prune` |

## Procedure

### 1. Classify request

- lifecycle: run/stop/start/restart/rm/pause/unpause
- interaction: exec/cp/logs/inspect/stats
- image: build/pull/push/tag/rmi/save/load
- Compose: up/down/ps/logs/exec/build/config
- volumes/networks: create/inspect/rm/prune/connect
- troubleshooting: logs, exit codes, resources

### 2. Container lifecycle

```bash
# Detached service with port mapping
docker run -d --name web -p 8080:80 nginx

# With environment variables
docker run -d -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=mydb --name db postgres:16

# With persistent data (named volume)
docker run -d -v pgdata:/var/lib/postgresql/data --name db postgres:16

# For development (bind mount source code)
docker run -d -v $(pwd)/src:/app/src -p 3000:3000 --name dev my-app

# Interactive debugging (auto-remove on exit)
docker run -it --rm ubuntu:22.04 /bin/bash

# With resource limits and restart policy
docker run -d --memory=512m --cpus=1.5 --restart=unless-stopped --name app my-app
```

Flags: `-d` detached; `-it` interactive+TTY; `--rm` auto-remove; `-p` host:container port; `-e` env; `-v` volume; `--name`; `--restart`.

```bash
docker ps                        # running containers
docker ps -a                     # all (including stopped)
docker stop NAME                 # graceful stop
docker start NAME                # start stopped container
docker restart NAME              # stop + start
docker rm NAME                   # remove stopped container
docker rm -f NAME                # force remove running container
docker container prune           # remove ALL stopped containers
```

Interact:

```bash
docker exec -it NAME /bin/sh          # shell access (use /bin/bash if available)
docker exec NAME env                   # view environment variables
docker exec -u root NAME apt update    # run as specific user
docker logs --tail 100 -f NAME         # follow last 100 lines
docker logs --since 2h NAME            # logs from last 2 hours
docker cp NAME:/path/file ./local      # copy file from container
docker cp ./file NAME:/path/           # copy file to container
docker inspect NAME                    # full container details (JSON)
docker stats --no-stream               # resource usage snapshot
docker top NAME                        # running processes
```

### 3. Images

```bash
# Build
docker build -t my-app:latest .
docker build -t my-app:prod -f Dockerfile.prod .
docker build --no-cache -t my-app .              # clean rebuild
DOCKER_BUILDKIT=1 docker build -t my-app .       # faster with BuildKit

# Pull and push
docker pull node:20-alpine
docker login ghcr.io
docker tag my-app:latest registry/my-app:v1.0
docker push registry/my-app:v1.0

# Inspect
docker images                          # list local images
docker history IMAGE                   # see layers
docker inspect IMAGE                   # full details

# Cleanup
docker image prune                     # remove dangling (untagged) images
docker image prune -a                  # remove ALL unused images (careful!)
docker image prune -a --filter "until=168h"   # unused images older than 7 days
```

### 4. Compose

```bash
# Start/stop
docker compose up -d                   # start all services detached
docker compose up -d --build           # rebuild images before starting
docker compose down                    # stop and remove containers
docker compose down -v                 # also remove volumes (DESTROYS DATA)

# Monitoring
docker compose ps                      # list services
docker compose logs -f api             # follow logs for specific service
docker compose logs --tail 50          # last 50 lines all services

# Interaction
docker compose exec api /bin/sh        # shell into running service
docker compose run --rm api npm test   # one-off command (new container)
docker compose restart api             # restart specific service

# Validation
docker compose config                  # validate and view resolved config
```

`down -v` destroys volumes; confirm first. Minimal example:

```yaml
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      # Password comes from the POSTGRES_PASSWORD secret, not the URL
      - DATABASE_URL=postgres://mydb_user@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### 5. Volumes/networks

```bash
# Volumes
docker volume ls                       # list volumes
docker volume create mydata            # create named volume
docker volume inspect mydata           # details (mount point, etc.)
docker volume rm mydata                # remove (fails if in use)
docker volume prune                    # remove unused volumes

# Networks
docker network ls                      # list networks
docker network create mynet            # create bridge network
docker network inspect mynet           # details (connected containers)
docker network connect mynet NAME      # attach container to network
docker network disconnect mynet NAME   # detach container
docker network rm mynet                # remove network
docker network prune                   # remove unused networks
```

### 6. Diagnose/clean disk

```bash
# Check what's using space
docker system df                       # summary
docker system df -v                    # detailed breakdown

# Targeted cleanup (safe)
docker container prune                 # stopped containers
docker image prune                     # dangling images
docker volume prune                    # unused volumes
docker network prune                   # unused networks

# Aggressive cleanup (confirm with user first!)
docker system prune                    # containers + images + networks
docker system prune -a                 # also unused images
docker system prune -a --volumes       # EVERYTHING — named volumes too
```

The last command removes named volumes and potentially important data; never run without confirmation.

## Pitfalls

Use the troubleshooting matrix below after inspection; confirm destructive cleanup before running it.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Container exits immediately | Main process finished or crashed | Check `docker logs NAME`, try `docker run -it --entrypoint /bin/sh IMAGE` |
| "port is already allocated" | Another process using that port | `docker ps` or `lsof -i :PORT` to find it |
| "no space left on device" | Docker disk full | `docker system df` then targeted prune |
| Can't connect to container | App binds to 127.0.0.1 inside container | App must bind to `0.0.0.0`, check `-p` mapping |
| Permission denied on volume | UID/GID mismatch host vs container | Use `--user $(id -u):$(id -g)` or fix permissions |
| Compose services can't reach each other | Wrong network or service name | Services use service name as hostname, check `docker compose config` |
| Build cache not working | Layer order wrong in Dockerfile | Put rarely-changing layers first (deps before source code) |
| Image too large | No multi-stage build, no .dockerignore | Use multi-stage builds, add `.dockerignore` |

## Verification

- started container: `docker ps`, status `Up`
- logs: `docker logs --tail 20 NAME`, no unexpected errors
- port: `curl -s http://localhost:PORT` or `docker port NAME`
- image: `docker images | grep TAG`
- Compose: `docker compose ps`, services `running`/`healthy`
- cleanup: compare `docker system df` before/after

## Dockerfile Optimization

1. multi-stage build separates build/runtime
2. dependencies before source for cache reuse
3. combine `RUN` commands where useful
4. `.dockerignore` excludes `node_modules`, `.git`, `__pycache__`, etc.
5. pin base versions (`node:20-alpine`, not `node:latest`)
6. run non-root with `USER`
7. use slim/alpine bases (`python:3.12-slim`, not `python:3.12`)
