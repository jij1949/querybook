---
name: lint
description: Lint and format code using pre-commit hooks (black, flake8, prettier) or individual tools.
argument_hint: "[--fix] [--python | --node | file path]"
---

# Lint Skill

Run linting and formatting checks for Querybook. Uses the same tools as pre-commit hooks.

## Determine What to Lint

Based on the user's input:

- **No arguments**: Run all linters (Python + JS/TS via pre-commit)
- **`--python`**: Run only Python linters
- **`--node`**: Run only JS/TS linters
- **`--fix`**: Auto-fix issues where possible
- **A file path**: Lint the specific file

## Run All Linters (Recommended)

Use pre-commit to run black, flake8, and prettier on all files:

```bash
.claude/scripts/run-in-venv.sh pre-commit run --all-files
```

## Python Linting

### Formatting (black)

```bash
# Check only
.claude/scripts/run-in-venv.sh black --check querybook/server/

# Auto-fix
.claude/scripts/run-in-venv.sh black querybook/server/
```

For a specific file:

```bash
.claude/scripts/run-in-venv.sh black querybook/server/path/to/file.py
```

**Note**: flake8 is run via pre-commit hooks only, not installed directly.

## TypeScript Linting

### ESLint

The `npm run lint` script includes `--fix` by default:

```bash
npm run lint
```

To lint a specific file without auto-fix:

```bash
npx eslint 'querybook/webapp/path/to/file.ts' --quiet
```

To lint with auto-fix:

```bash
npx eslint 'querybook/webapp/path/to/file.ts' --quiet --fix
```

### TypeScript Type Checking

```bash
npm run tsc-check
```

## Behavior

- When `--fix` is specified, run formatters/fixers. Otherwise, run in check mode.
- Report errors and warnings with file paths and line numbers.
- If there are auto-fixable issues and `--fix` was not specified, suggest running with `--fix`.
