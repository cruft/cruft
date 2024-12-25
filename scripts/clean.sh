#!/bin/bash
set -euxo pipefail

poetry run ruff format cruft/ tests/
poetry run ruff check --fix --unsafe-fixes cruft/ tests/
