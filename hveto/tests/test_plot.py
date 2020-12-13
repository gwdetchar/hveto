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

import os
import pytest
import shutil

from numpy import random

from matplotlib import use
use('agg')

from .. import plot  # noqa: E402


@pytest.mark.parametrize('num', (10, 50, 200))
def test_drop_plot(num, tmpdir):
    random.seed(0)
    outdir = str(tmpdir)
    # this test just makes sure the drop plot code runs end-to-end
    channels = ['X1:TEST-%d' % i for i in range(num)]
    old = dict(zip(channels, random.normal(size=num)))
    new = dict(zip(channels, random.normal(size=num)))
    # test PNG files
    plot.significance_drop(os.path.join(outdir, 'test.png'),
                           old, new)
    # test SVG files, which raise UserWarnings
    with pytest.warns(UserWarning) as record:
        plot.significance_drop(os.path.join(outdir, 'test.svg'),
                               old, new)
    for rec in record:
        assert rec.message.args[0].startswith("Failed to recover tooltip")
    # clean up
    shutil.rmtree(outdir, ignore_errors=True)
