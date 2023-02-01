#!/bin/bash
set -euxo pipefail

poetry run cruft check
poetry run mypy --ignore-missing-imports cruft/
poetry run isort --check --diff cruft/ tests/
poetry run black --check cruft/ tests/
poetry run flake8 cruft/ tests/
# Safety won't allow installations for tornado<=6.1
# but tornade 6.1 is the latest.
# Run safety checks with warnings only
poetry run safety check -i 39462 -i 40291 -i 47794 -i 50571 || true
poetry run bandit -r cruft/
