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

import os
import shutil
from tempfile import NamedTemporaryFile

import pytest

from gwpy.testing.compat import mock
from gwpy.segments import (Segment, SegmentList,
                           DataQualityFlag, DataQualityDict)

from .. import segments

TEST_SEGMENTS = SegmentList([
    Segment(0.1, 1.234567),
    Segment(5.64321, 6.234567890),
])
TEST_SEGMENTS_2 = SegmentList([Segment(round(a, 6), round(b, 6)) for
                               a, b in TEST_SEGMENTS])

TEST_FLAG = DataQualityFlag(
    known=SegmentList([Segment(0, 7)]),
    active=TEST_SEGMENTS,
    name='X1:TEST-FLAG')
TEST_DICT = DataQualityDict({
    TEST_FLAG.name: TEST_FLAG})


# -- unit tests ---------------------------------------------------------------

@mock.patch('gwpy.segments.DataQualityFlag.query', return_value=TEST_FLAG)
def test_query(dqflag):
    flag = segments.query('X1:TEST-FLAG', 0, 7)
    assert flag.known == TEST_FLAG.known
    assert flag.active == SegmentList([
        Segment((int(seg[0]), int(seg[1]))) for seg in TEST_FLAG.active])


@pytest.mark.parametrize('ncol', (2, 4))
def test_write_segments_ascii(ncol):
    with NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        segments.write_ascii(tmp.name, TEST_SEGMENTS, ncol=ncol)
        tmp.delete = True
        a = SegmentList.read(tmp.name, gpstype=float, strict=False)
        assert a == TEST_SEGMENTS_2


def test_write_segments_ascii_failure():
    with pytest.raises(ValueError) as exc:
        segments.write_ascii('test.txt', TEST_SEGMENTS, ncol=42)
    assert str(exc.value).startswith('Invalid number of columns')


@mock.patch('gwpy.segments.DataQualityDict.from_veto_definer_file')
def test_read_veto_definer_file(dqflag, tmpdir):
    dqflag.return_value = TEST_DICT
    os.chdir(str(tmpdir))
    testfile = 'https://www.w3.org/TR/PNG/iso_8859-1.txt'
    dqdict = segments.read_veto_definer_file(testfile)
    assert dqdict == TEST_DICT
    shutil.rmtree(str(tmpdir), ignore_errors=True)
