# Contributing to Querybook

This guide covers everything a human contributor needs to set up, build, test, and
run Querybook locally. For project architecture and code patterns, see
[`AGENTS.md`](AGENTS.md); for how to work effectively with AI assistants in this
repo, see [`HOWTOAI.md`](HOWTOAI.md).

## Prerequisites

-   **Docker** — required for the quickest path to a running instance and for the
    containerized test suite.
-   **Node.js >= 18** (see `engines` in `package.json`) with `yarn`.
-   **Python 3.10.16** (recommended; used by the `/setup` skill), managed with `pyenv`
    (`brew install pyenv`) for local backend development and tests.

## Quick Start (Docker)

The fastest way to run Querybook is via Docker Compose:

```bash
make
```

This builds the dev image and runs `docker compose --profile all --profile
vectorstore up`. When the build completes, visit <http://localhost:10001>.

For installation details, see the
[setup guide](docs_website/docs/setup_guide/overview.mdx).

### Other Docker run modes

The `Makefile` provides targets backed by `containers/docker-compose.dev.yml`:

| Target | What it runs |
| --- | --- |
| `make web` | Dev web server (rebuilds dev image, kills any running dev server first) |
| `make worker` | Celery worker |
| `make scheduler` | Celery beat scheduler |
| `make terminal` | Interactive container shell |
| `make bundled_off` | Tear down the bundled stack |

A `/docker` Claude Code skill is available to manage the Docker dev environment
(start/stop services, view logs, connect to containers, reset volumes).

## Local Python Environment

For running backend tests and tooling outside Docker, set up a virtualenv. The
`/setup` Claude Code skill automates this; the equivalent manual steps:

```bash
# 1. Install and pin the Python version
pyenv install 3.10.16
pyenv local 3.10.16

# 2. Create and activate a virtualenv
python -m venv .virtualenv
source .virtualenv/bin/activate

# 3. Install runtime + test dependencies
pip install -r requirements.txt
pip install -r requirements/test.txt
```

The `requirements/` directory holds composable dependency sets (`base.txt`,
`dev.txt`, `test.txt`, plus `engine/`, `metastore/`, `auth/`, `ai/`, `platform/`,
etc.). For extra services needed in local development, create a gitignored
`requirements/local.txt` that includes the sets you need (e.g.
`-r engine/trino.txt`, `-r metastore/hms.txt`), then
`pip install -r requirements/local.txt`.

A helper script activates the virtualenv for one-off commands:

```bash
.claude/scripts/run-in-venv.sh <command>
```

## Frontend Dependencies

```bash
make install            # installs pip runtime deps + yarn packages
# or, for JS only:
yarn install --frozen-lockfile
```

## Build

```bash
yarn build              # production webpack build (npx webpack)
yarn dev                # webpack dev server with hot reload
```

## Lint & Format

Linting and formatting use pre-commit hooks (black, flake8, prettier) plus the JS
ESLint config. A `/lint` Claude Code skill wraps these.

```bash
yarn lint               # ESLint over the TypeScript sources (with --fix)
yarn tsc-check          # TypeScript type check (tsc --noEmit)
```

## Tests

A `/test` Claude Code skill runs the suite; the underlying commands:

```bash
# All tests (Python + TS validation + Jest + ESLint + webpack build), local:
.claude/scripts/run-in-venv.sh ./querybook/scripts/run_test

# Python only:
.claude/scripts/run-in-venv.sh ./querybook/scripts/run_test --python

# A specific Python test file:
.claude/scripts/run-in-venv.sh env PYTHONPATH=querybook/server:plugins pytest querybook/tests/test_lib/test_metastore/test_loaders/test_glue_data_catalog_loader.py -v

# JS/TS tests:
yarn test
yarn test -- table-identifier.test.ts   # a single file
yarn test -- --watch                    # watch mode
```

To run the full suite in an isolated container (thorough but slow):

```bash
make test               # docker-compose -f containers/docker-compose.test.yml up --abort-on-container-exit
```

## Database Migrations

Database migrations use Alembic (config at `querybook/alembic.ini`, migrations in
`querybook/migrations/`).

## Local Development: AWS Authentication (Glue Metastore)

When connecting to a Glue metastore locally, authenticate using `okta-aws-cli`
with a profile configured in `~/.okta/okta.yaml`.

Log in to the dataplatform test profile:

```bash
okta-aws-cli --profile egdataplatform-test-pwu
```

Verify the credentials work:

```bash
aws --profile egdataplatform-test-pwu s3 ls
```

More documentation:
<https://expediagroup.atlassian.net/wiki/spaces/IAM/pages/560567507/AWS+CLI>

## Documentation Site

The public docs (querybook.org) are a Docusaurus site under `docs_website/`. To run
it locally:

```bash
make docs                # docker-compose -f docs_website/docker-compose.yml up --build
```

## Pull Requests

This repo uses release-please and conventional commits (see
`release-please-config.json` and `.releaserc.yml`). Write clear commit messages
using conventional-commit prefixes (`feat:`, `fix:`, `chore:`, etc.). Run lint and
tests before opening a PR.

## Useful Make Targets

Run `make <target>`:

-   `make install` — install pip runtime deps + yarn packages
-   `make clean` — remove `.pyc`/`__pycache__` files and prune Docker volumes
-   `make prod_image` / `make prod_web` / `make prod_worker` / `make prod_scheduler`
    — production image and run modes
