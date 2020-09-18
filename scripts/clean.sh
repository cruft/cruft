#!/bin/bash
set -euxo pipefail

poetry run isort cruft/ tests/
poetry run black cruft/ tests/
