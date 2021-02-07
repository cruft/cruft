#!/bin/bash
set -euxo pipefail

# set nocasematch option
shopt -s nocasematch

# Declare an array (of type string).
declare -a XTRA_COV=()
declare XTRA_OPT=""

if [[ $OSTYPE =~ ^msys|^WIN ]]; then
    # XTRA_OPT="-x --count 10"
    XTRA_OPT="--count 5"
else
    XTRA_COV+=("pragma: no cov_4_nix")
fi

# Iterate the string array using for loop. The quotes ensure iteration
# over multiple words string. It's important that .coverage ends with an empty last line.
cp -f ./scripts/.coveragerc_source ./.coveragerc
for val in "${XTRA_COV[@]}"; do
   echo "    $val" >> .coveragerc
done


poetry run pytest -s -n auto --cov=cruft/ --cov=tests --cov-report=term-missing ${@-} --cov-report xml --cov-report html $XTRA_OPT

./scripts/lint.sh
