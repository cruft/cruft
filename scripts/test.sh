#!/bin/bash
set -euxo pipefail

poetry run pytest -s -n auto --cov=cruft/ --cov=tests --cov-report=term-missing ${@-} --cov-report xml --cov-report html
./scripts/lint.sh
