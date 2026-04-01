---
name: test
description: Run unit tests for this project. Use after implementing changes, fixing bugs, or when verifying existing behavior. Supports running all tests, Python-only, JS-only, or individual test files.
argument_hint: "[--python | --node | file path]"
---

# Test Skill

Run backend (Python) and frontend (JS/TS) tests for Querybook.

Tip: Ask the user to approve running `.claude/scripts/run-in-venv.sh` first to make it easier to run.

## Prerequisites

A local Python virtualenv with test dependencies is required for Python tests. See `/setup` for full environment setup including pyenv, optional extras, and Node dependencies.

## Determine What to Test

Based on the user's input:

- **No arguments**: Run all tests (Python + JS)
- **`--python`**: Run only Python tests
- **`--node`**: Run only JS/TS tests
- **A file path**: Run the specific test file

## Running Tests (Local — Recommended)

### Python Tests

```bash
.claude/scripts/run-in-venv.sh ./querybook/scripts/run_test --python
```

To run a specific test file or directory with pytest directly:

```bash
.claude/scripts/run-in-venv.sh pytest querybook/tests/test_lib/test_metastore/test_base_loader.py -v
```

### JS/TS Tests

```bash
npm run test
```

To run a specific test file:

```bash
npm run test -- table-identifier.test.ts
```

To run in watch mode:

```bash
npm run test -- --watch
```

### All Tests (Python + JS/TS)

```bash
.claude/scripts/run-in-venv.sh ./querybook/scripts/run_test
```

This runs Python tests, TypeScript validation, Jest tests, ESLint, and webpack build in parallel.

## Running Tests (Docker — Slow)

Builds a dedicated test image and runs the full suite in an isolated container. This is thorough but slow — prefer the local approach above for day-to-day development.

```bash
make test
```

This runs `docker-compose --file containers/docker-compose.test.yml up --abort-on-container-exit`.

## Reporting Results

After running tests:
- Report the number of tests passed/failed
- If tests fail, show the relevant failure output
- Suggest fixes if the failures are clearly related to recent changes
