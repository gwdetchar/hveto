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

"""Tests for `hveto.triggers`
"""

import pytest

from astropy.table import Table

from gwpy.segments import (Segment, SegmentList)

from .. import triggers

AUX_FILES = {
    'L1:GDS-CALIB_STRAIN': 'L1-GDS_CALIB_STRAIN_OMICRON-12345-67890.xml.gz',
    'H1:SUS-BS_M1_MASTER_OUT_F2_DQ_0_DAC':
        'H1-SUS_BS_M1_MASTER_OUT_F2_DQ_0_DAC-1126252143-22179.xml.gz',
}


def test_aux_channels_from_cache():
    cache = list(AUX_FILES.values())
    channels = triggers.find_auxiliary_channels(
        'omicron', None, None, cache=cache)
    assert channels == sorted(AUX_FILES.keys())

    channels = triggers.find_auxiliary_channels(
        'omicron', None, None, cache=cache)
    assert channels == sorted(AUX_FILES.keys())


def test_get_triggers():
    # test that trigfind raises a warning if the channel-level directory
    # doesn't exist
    with pytest.warns(UserWarning):
        out = triggers.get_triggers('X1:DOES_NOT_EXIST', 'omicron',
                                    SegmentList([Segment(0, 100)]))
    # check output type and columns
    assert isinstance(out, Table)
    for col in ['time', 'frequency', 'snr']:
        assert col in out.dtype.names
