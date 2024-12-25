#!/bin/bash
set -euxo pipefail

uv run cruft check
uv run ruff check cruft/ tests/
uv run ruff format --check cruft/ tests/
