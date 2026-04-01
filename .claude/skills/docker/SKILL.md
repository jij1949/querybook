---
name: docker
description: Manage the Querybook Docker development environment. Start/stop services, view logs, connect to containers, and reset volumes.
argument_hint: "[up | down | logs | exec | reset | status | build]"
---

# Docker Skill

Manage the Querybook Docker Compose development environment.

## Commands

Based on the user's input:

### `up` (default if no arguments)

Start the full development stack. This builds the dev image if needed and launches all services (web, worker, scheduler, MySQL, Redis, Elasticsearch).

```bash
make
```

This runs `docker compose --profile all --profile vectorstore up`.

To start specific profiles only:

```bash
# Just web + infra
docker compose --profile web --profile infra up

# Just infra (MySQL, Redis, Elasticsearch)
docker compose --profile infra up

# MCP server + dependencies
docker compose --profile mcp up

# Flower (Celery monitoring)
docker compose --profile flower up
```

The web UI is available at http://localhost:10001.

### `down`

Stop all running containers:

```bash
docker compose down
```

### `reset`

Stop containers AND delete all volumes (MySQL data, Elasticsearch indices). This gives a completely fresh environment.

**IMPORTANT: Always confirm with the user before running this — it destroys all local data.**

```bash
docker compose down --volumes
```

### `logs`

View logs for a specific service or all services:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f mcp
```

### `exec`

Connect to a running container:

```bash
docker exec -it querybook_web bash
docker exec -it querybook_worker bash
docker exec -it querybook_mcp bash
```

### `status`

Show running containers:

```bash
docker compose ps
```

### `build`

Rebuild Docker images:

```bash
make dev_image    # Development image
make prod_image   # Production image
make test_image   # Test image
```

## Docker Compose Profiles

| Profile | Services |
|---------|----------|
| `all` | web, worker, scheduler, mcp, redis, mysql, elasticsearch |
| `web` | web only |
| `worker` | worker only |
| `infra` | scheduler, redis, mysql, elasticsearch |
| `mcp` | mcp, worker, redis, mysql, elasticsearch |
| `flower` | Celery monitoring UI (port 5566) |
| `vectorstore` | Elasticsearch 8 for vector search (port 9201) |
| `extras` / `kibana` | Kibana UI (port 5601) |

## Environment Variables

Additional env vars can be set in `.env.local` (gitignored). These are passed to web/worker/scheduler/mcp containers. See the Confluence dev guide for recommended values.

## Additional Requirements

The dev image only includes base requirements. To install extras (Trino client, HMS, etc.), create `requirements/local.txt` (gitignored) — it is auto-installed during `make`.

## Database Migrations

To run Alembic migrations inside the container:

```bash
docker exec -it querybook_web bash
cd querybook
PYTHONPATH=server alembic revision --autogenerate -m "description"
PYTHONPATH=server alembic upgrade head
```
