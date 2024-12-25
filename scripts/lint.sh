#!/bin/bash
set -euxo pipefail

poetry run cruft check
poetry run ruff check cruft/ tests/
poetry run ruff format --check cruft/ tests/
