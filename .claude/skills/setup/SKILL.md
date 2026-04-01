---
name: setup
description: Set up local Python virtualenv for Querybook development. Installs Python via pyenv, creates virtualenv, and installs dependencies.
argument_hint: ''
---

# Setup Skill

Set up a local Python environment for Querybook development and testing. This doesn't have to be done more than once, but if anything is broken, refer back to this guide to verify your setup.

## Prerequisites

-   pyenv (`brew install pyenv`) with shell integration configured
-   Node.js >= 18

## Python Setup

### 1. Install and activate the correct Python version

```bash
pyenv install 3.10.16
pyenv local 3.10.16
python --version
```

### 2. Create a virtual environment

```bash
python -m venv .virtualenv
source .virtualenv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements/test.txt
```

### 4. (Optional) Install extra requirements for local development

Create `requirements/local.txt` (gitignored) for additional dependencies needed to connect to real services:

```
# Recommended for EGAP development
-r engine/trino.txt
-r engine/hive.txt
-r engine/bigquery.txt
-r metastore/hms.txt
-r platform/aws.txt
-r auth/ldap.txt
-r auth/oauth.txt
-r ai/langchain.txt
-r github_integration/github.txt
```

Then install:

```bash
pip install -r requirements/local.txt
```

## Node Setup

```bash
yarn install --ignore-scripts --frozen-lockfile --pure-lockfile --ignore-engines
```

Or via make:

```bash
make install
```

## Verify Setup

```bash
source .virtualenv/bin/activate
PYTHONPATH=querybook/server ./querybook/scripts/run_test --python
npm run test
```
