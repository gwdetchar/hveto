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
import tempfile

from matplotlib import use
use('agg')

from numpy import random

from hveto import plot

from common import unittest


class PlotTestCase(unittest.TestCase):
    def setUp(self):
        self.tempfileid, self.tempfile = tempfile.mkstemp(suffix='.png')

    def tearDown(self):
        if os.path.isfile(self.tempfile):
            os.remove(self.tempfile)

    def test_drop_plot(self):
        # this test just makes sure the drop plot code runs end-to-end
        for x in [10, 50, 200]:
            channels = ['X1:TEST-%d' % i for i in range(x)]
            old = dict(zip(channels, random.normal(size=x)))
            new = dict(zip(channels, random.normal(size=x)))
            plot.significance_drop(self.tempfile, old, new)
            svg = self.tempfile.replace('.png', '.svg')
            try:
                plot.significance_drop(svg, old, new)
            finally:
                if os.path.isfile(svg):
                    os.remove(svg)
