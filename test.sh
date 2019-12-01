#!/bin/sh

set -e
set -x

# Run test suite with coverage checks
#
coverage3 erase
coverage3 run --branch --source pihat setup.py test
coverage3 report --show-missing

# Run mypy
#
mypy pihat test

# Run pycodestyle
#
python3 -m pycodestyle pihat test

# Run pylint
#
pylint pihat test
