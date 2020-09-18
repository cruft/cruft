#!/bin/bash
set -euxo pipefail

poetry run cruft check
poetry run mypy --ignore-missing-imports cruft/
poetry run isort --check --diff cruft/ tests/
poetry run black --check cruft/ tests/
poetry run flake8 cruft/ tests/
poetry run safety check
poetry run bandit -r cruft/
poetry run cruft check
