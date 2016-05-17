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

"""Tests for `hveto.segments`
"""

from tempfile import NamedTemporaryFile

from gwpy.segments import (Segment, SegmentList)

from hveto import segments

from common import unittest

TEST_SEGMENTS = SegmentList([
    Segment(0.1, 1.234567),
    Segment(5.64321, 6.234567890),
])
TEST_SEGMENTS_2 = SegmentList([Segment(round(a, 6), round(b, 6)) for
                               a, b in TEST_SEGMENTS])


class SegmentsTestCase(unittest.TestCase):
    def test_write_segments_ascii(self):
        for ncol in [2, 4]:
            with NamedTemporaryFile(suffix='.txt', delete=False) as f:
                segments.write_ascii(f.name, TEST_SEGMENTS, ncol=ncol)
                f.delete = True
                a = SegmentList.read(f.name, gpstype=float, strict=False)
                self.assertEqual(a, TEST_SEGMENTS_2)
