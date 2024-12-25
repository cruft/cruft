#!/bin/bash
set -euxo pipefail

uv run ruff format cruft/ tests/
uv run ruff check --fix --unsafe-fixes cruft/ tests/
