#!/bin/sh

set -e
set -x

# Run test suite with coverage checks
#
python3 -m coverage erase
python3 -m coverage run --branch --source pihat setup.py test
python3 -m coverage report --show-missing

# Run mypy
#
python3 -m mypy pihat test

# Run pycodestyle
#
python3 -m pycodestyle pihat test

# Run pylint
#
python3 -m pylint pihat test
