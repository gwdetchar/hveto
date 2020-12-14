# -*- coding: utf-8 -*-
# Copyright (C) Alex Urban (2020)
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

"""Tests for :mod:`hveto.cli.trace`
"""

import os.path
import pytest
import shutil

from gwpy.segments import (
    Segment,
    SegmentList,
)

from .. import trace

__author__ = "Alex Urban <alexander.urban@ligo.org>"


# -- test configuration

VALID_RESULTS = """{
  "rounds": [{
    "files": {"VETO_SEGS": ["TEST-HVETO-SEGMENTS.txt"]},
    "name": "L1:ASC-X_TR_A_NSUM_OUT_DQ",
    "significance": 78.93832125380759,
    "snr": 11.0,
    "window": 0.4
  }]
}"""

EMPTY_RESULTS = '{"rounds": [{"files": {"VETO_SEGS": []}}]}'
TEST_SEGMENTS = SegmentList([Segment(0, 8)])


# -- cli tests ----------------------------------------------------------------

def test_main(caplog, tmpdir):
    indir = str(tmpdir)
    summary_stats = os.path.join(indir, 'summary-stats.json')
    print(VALID_RESULTS, file=open(summary_stats, 'w'))
    TEST_SEGMENTS.write(os.path.join(indir, 'TEST-HVETO-SEGMENTS.txt'))
    args = [
        '--trigger-time', '4',
        '--directory', indir,
        '--verbose',
    ]
    # test output
    trace.main(args)
    assert "Running in verbose mode" in caplog.text
    assert "Search directory: {}".format(indir) in caplog.text
    assert ("Trigger time 4.0 was vetoed in round 1 "
            "by segment [0 ... 8)" in caplog.text)
    assert "Round winner: L1:ASC-X_TR_A_NSUM_OUT_DQ" in caplog.text
    assert "Significance: 78.93832125380759" in caplog.text
    assert "SNR: 11.0" in caplog.text
    assert "Window: 0.4" in caplog.text
    # clean up
    shutil.rmtree(indir, ignore_errors=True)


def test_main_no_input(caplog, tmpdir):
    indir = str(tmpdir)
    args = [
        '--trigger-time', '0',
        '--directory', indir,
    ]
    # test output
    with pytest.raises(IOError):
        trace.main(args)
    assert ("'summary-stats.json' was not found in the "
            "input directory" in caplog.text)
    # clean up
    shutil.rmtree(indir, ignore_errors=True)


def test_main_empty_input(caplog, tmpdir):
    indir = str(tmpdir)
    summary_stats = os.path.join(indir, 'summary-stats.json')
    print(EMPTY_RESULTS, file=open(summary_stats, 'w'))
    args = [
        '--trigger-time', '0',
        '--directory', indir,
    ]
    # test output
    trace.main(args)
    assert "Trigger time 0.0 was not vetoed" in caplog.text
    # clean up
    shutil.rmtree(indir, ignore_errors=True)
