#!/bin/bash
set -euxo pipefail

./scripts/lint.sh
poetry run pytest -s -n auto --cov=cruft/ --cov=tests --cov-report=term-missing ${@-} --cov-report xml --cov-report html
