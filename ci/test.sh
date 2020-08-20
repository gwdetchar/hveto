#!/bin/bash
# Copyright (C) Duncan Macleod (2017-2020)
#
# This file is part of Hveto.
#
# Hveto is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hveto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hveto.  If not, see <http://www.gnu.org/licenses/>.

set -ex
trap 'set +ex' RETURN

#
# Run the test suite for Hveto on the current system
#

# reactivate environmennt
if [ -n ${CIRCLECI} ] && [ -d /opt/conda/envs ]; then
    conda activate hvetoci || source activate hvetoci
fi

# get path to python and pip
PYTHON=$(which "python${PYTHON_VERSION}")
PIP="${PYTHON} -m pip"

# upgrade pip to understand python_requires
${PIP} install "pip>=9.0.0"

# upgrade setuptools to understand environment markers
${PIP} install "setuptools>=20.2.2" wheel

# list all packages
if [ -z ${CONDA_PREFIX} ]; then
    ${PIP} list installed
else
    conda list --name hvetoci
fi

# run flake8 linter
${PYTHON} -m flake8 hveto
${PYTHON} -m flake8 bin/*

# run standard test suite
${PYTHON} -m coverage run -m pytest hveto

# test command-line utilities
${PYTHON} -m coverage run --append `which hveto` --help
${PYTHON} -m coverage run --append `which hveto-cache-events` --help
${PYTHON} -m coverage run --append `which hveto-trace` --help
