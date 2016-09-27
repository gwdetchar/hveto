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

"""Tests for `hveto.core`
"""

from hveto import core

from common import unittest


class HvetoRoundTestCase(unittest.TestCase):
    def test_init(self):
        r = core.HvetoRound(1, 'X1:PRIMARY')
        self.assertEqual(r.n, 1)
        self.assertEqual(r.primary, 'X1:PRIMARY')


class CoreTestCase(unittest.TestCase):
    def test_significance(self):
        self.assertAlmostEqual(core.significance(1, 1), 0.19920008462778135)
        self.assertAlmostEqual(core.significance(100, 10), 62.26771967596927)
        self.assertEqual(core.significance(1, 100), 0.0)
