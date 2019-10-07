# -*- coding: utf-8 -*-
# Copyright (C) Joshua Smith (2016-)
#
# This file is part of the hveto python package.
#
# hveto is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hveto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hveto.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for `hveto.plot`
"""

import tempfile

import pytest

from matplotlib import use
use('agg')  # noqa

from numpy import random

from .. import plot


@pytest.mark.parametrize('num', (10, 50, 200))
def test_drop_plot(num):
    random.seed(0)
    # this test just makes sure the drop plot code runs end-to-end
    channels = ['X1:TEST-%d' % i for i in range(num)]
    old = dict(zip(channels, random.normal(size=num)))
    new = dict(zip(channels, random.normal(size=num)))
    with tempfile.NamedTemporaryFile(suffix='.png') as png:
        plot.significance_drop(png.name, old, new)

    with tempfile.NamedTemporaryFile(suffix='.svg') as svg:
        plot.significance_drop(svg.name, old, new)
