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

"""Tests for :mod:`hveto.core`
"""

import pytest

from .. import core


def test_create_round():
    """Test creation of a `hveto.core.HvetoRound` object
    """
    r = core.HvetoRound(1, 'X1:PRIMARY')
    assert r.n == 1
    assert r.primary == 'X1:PRIMARY'


@pytest.mark.parametrize('n, mu, sig', [
    (1, 1, 0.19920008462778135),
    (100, 10, 62.26771967596927),
    (1, 100, 0.0),
])
def test_significance(n, mu, sig):
    """Test :func:`hveto.core.significance`
    """
    assert core.significance(n, mu) == pytest.approx(sig)
