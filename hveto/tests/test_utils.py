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

"""Tests for `hveto.utils`
"""

from hveto import utils

from common import unittest


class UtilsTestCase(unittest.TestCase):
    def test_channel_groups(self):
        self.assertListEqual(list(utils.channel_groups([1, 2, 3, 4, 5], 1)),
                             [[1, 2, 3, 4, 5]])
        self.assertListEqual(list(utils.channel_groups([1, 2, 3, 4, 5], 2)),
                             [[1, 2, 3], [4, 5]])
        self.assertListEqual(list(utils.channel_groups([1, 2, 3, 4, 5], 10)),
                             [[1], [2], [3], [4], [5]])
