#!/bin/bash
set -euxo pipefail

# set nocasematch option
shopt -s nocasematch

# Declare an array (of type string).
declare XTRA_OPT=""

if [[ $OSTYPE =~ ^msys|^WIN ]]; then
    if [[ $* == *--ci* ]]; then
      XTRA_OPT="--count 5"
    fi
fi

if [[ $* == *--ci* ]]; then
  shift
fi

uv run pytest -s -n auto --cov=cruft/ --cov=tests --cov-report=term-missing ${@-} --cov-report xml --cov-report html $XTRA_OPT
./scripts/lint.sh
