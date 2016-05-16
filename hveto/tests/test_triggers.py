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

import numpy

from glue.lal import Cache

from gwpy.segments import (Segment, SegmentList)

from hveto import triggers

from common import unittest

AUX_FILES = {
    'L1:GDS-CALIB_STRAIN': 'L1-GDS_CALIB_STRAIN_OMICRON-12345-67890.xml.gz',
    'H1:SUS-BS_M1_MASTER_OUT_F2_DQ_0_DAC':
        'H1-SUS_BS_M1_MASTER_OUT_F2_DQ_0_DAC-1126252143-22179.xml.gz',
}


class TriggersTestCase(unittest.TestCase):

    def test_aux_channels_from_cache(self):
        cache = Cache.from_urls(AUX_FILES.values())
        channels = triggers.find_auxiliary_channels('omicron', None, None,
                                                    cache=cache)
        self.assertListEqual(channels, sorted(AUX_FILES.keys()))

    def test_get_triggers(self):
        # test that trigfind raises a warning if the channel-level directory
        # doesn't exist
        with pytest.warns(UserWarning):
            out = triggers.get_triggers('X1:DOES_NOT_EXIST', 'omicron',
                                        SegmentList([Segment(0, 100)]))
        # check output type and columns
        self.assertIsInstance(out, numpy.ndarray)
        for col in ['time', 'frequency', 'snr']:
            self.assertIn(col, out.dtype.fields)
        # test that unknown ETG raises KeyError
        self.assertRaises(KeyError, triggers.get_triggers,
                          'X1:DOES_NOT_EXIST', 'fake-etg',
                          SegmentList([Segment(0, 100)]))
