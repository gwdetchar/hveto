# -*- coding: utf-8 -*-
# Copyright (C) Siddharth Soni (2020-)
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

"""Constants for `hveto.utils`
"""

import os
from gwpy.time import from_gps

__author__ = 'Siddharth Soni <siddharth.soni@ligo.org>'


def get_hvetopath(gpstime):
    """ Returns the path of hveto output files

    Given a gpstime, the path of the folder
    containing hveto trigger files is returned

    Parameters
    ----------
    gpstime : `str` or `float`
        start time of the day for this analysis

    Returns
    _______
    path : `str`
        path to the hveto output file on the local filesystem

    Example
    _______
    >>> from hveto.const import get_hvetopath
    >>> get_hvetopath(1257811218)
    '/home/detchar/public_html/hveto/day/20191115/latest'
    """
    date = from_gps(gpstime).strftime('%Y%m%d')
    # the following hveto_dir path exists for normal Detchar workflow
    # at LHO and LLO computing clusters
    hveto_dir = '/home/detchar/public_html/hveto/day/'
    path = os.path.join(hveto_dir, date, 'latest')
    return path
