#!/usr/bin/env bash

# Get the directory where this script lives
DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$DIR"
[[ ! -d "venv" ]] && python3 -m venv venv && venv/bin/pip3 install pip wheel --upgrade
pip_args=(--upgrade)
PYTHON="python3"
PIP="venv/bin/pip3"
if [[ $(uname) =~ "MINGW" ]]; then
    PYTHON="python"
    PIP="venv/Scripts/pip"
fi
[[ ! -d "venv" ]] && $PYTHON -m venv venv && $PIP install wheel pip ${pip_args[@]}
pip_version=$($PIP --version | egrep -o 'pip (\d+)' | cut -c 5-)
[[ -z "$pip_version" ]] && pip_version=$($PIP --version | perl -pe 's/^pip\s+(\d+).*/$1/')
[[ -z "$pip_version" ]] && pip_version=0;
[[ $pip_version -gt 9 ]] && pip_args=(--upgrade --upgrade-strategy eager)
$PIP install -r requirements.txt ${pip_args[@]}
if [[ ! $(uname) =~ "MINGW" ]]; then
    $PIP install ipython pdbpp ${pip_args[@]}
else
    $PIP install ipython ${pip_args[@]}
fi
PYTHON=$(dirname $PIP)/python
$PYTHON setup.py develop
