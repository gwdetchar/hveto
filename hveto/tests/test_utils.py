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

import pytest

from gwpy.io.cache import read_cache

from .. import utils


def test_write_lal_cache(tmpdir):
    cache = [
        "/test/path/X-TEST-0-1.txt",
        "/test/path/X-TEST-2-3.txt",
    ]
    target = tmpdir.join("cache.lcf")
    utils.write_lal_cache(str(target), cache)
    assert read_cache(str(target)) == cache


@pytest.mark.parametrize('n, out', [
    (1, [[1, 2, 3, 4, 5]]),
    (2, [[1, 2, 3], [4, 5]]),
    (10, [[1], [2], [3], [4], [5]]),
])
def test_channel_groups(n, out):
    assert list(utils.channel_groups([1, 2, 3, 4, 5], n)) == out
