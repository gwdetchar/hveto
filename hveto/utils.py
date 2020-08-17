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

"""General utilities for hveto
"""

from math import ceil

from gwdatafind.utils import filename_metadata
import pandas as pd
import numpy
from gwpy.time import from_gps, to_gps
from gwpy.segments import Segment
import argparse
import time
import glob
import os
import datetime as dt

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'


def write_lal_cache(target, paths):
    # if not an open file, open it
    if isinstance(target, str):
        with open(target, "w") as fobj:
            write_lal_cache(fobj, paths)
            return target

    # write to file
    for path in paths:
        obs, tag, segment = filename_metadata(path)
        print(obs, tag, segment[0], abs(segment), path, file=target)

    return target


# -- utilities ----------------------------------------------------------------

def channel_groups(channellist, ngroups):
    """Separate a list of channels into a number of equally-sized groups

    Parameters
    ----------
    channellist : `list`
        large list to separate into chunks
    ngroups : `int`
        number of output groups

    Returns
    -------
    iterator : iterator `list` of `list`
        a generator sequence yielding a sub-list on each iteration
    """
    n = int(ceil(len(channellist) / ngroups))
    for i in range(0, len(channellist), n):
        yield channellist[i:i+n]


def primary_vetoed(starttime, endtime, ifo, snr=6.0, significance=5.0,
                   output_dir=os.curdir):

    """Finds all the vetoed primary triggers and the auxiliary winner
       channel between two gpstimes vetoed by hveto. The data includes
       the gpstime, snr, peak frequency of the primary trigger and the
       hveto significance of the correlation between the noise in auxiliary
       and primary channel.
       SNR and significance threshold can be used to query the data.

       Returns
       -------
       pandas dataframe and saves the csv file in the output directory"""

    startdate = from_gps(starttime).date()
    enddate = from_gps(endtime).date()

    filename = output_dir+'hveto_primary_{}_{}.csv'.format(starttime, endtime)
    #Getting all the dates in string format
    delta = enddate - startdate
    days = delta.days
    dates_final = [(startdate + dt.timedelta(i)).strftime('%Y%m%d') for i in
                   range(days)]
    #Getting the Vetoed triggers files for each day
    dfwhole = pd.DataFrame()
    for j in dates_final:
        hveto_path = '/home/detchar/public_html/hveto/day/' + j + '/latest/'
    #files = glob.glob(hveto_path+'triggers/'+ '/*VETOED*.txt')

        try:
            files = glob.glob(hveto_path+'triggers/' + '/*VETOED*.txt')
            df = pd.read_csv(hveto_path + 'summary-stats.txt', sep=" ")
            n = len(df)
            files = files[:n]
            dfday = pd.DataFrame()
            for i in range(n):
                dfvetoed = pd.read_csv(files[i], sep=" ")
                dfvetoed['winner'] = df['winner'].iloc[i]
                dfvetoed['significance'] = df['significance'].iloc[i]
                dfday = dfday.append(dfvetoed)
            dfday = dfday.reset_index(drop=True)

            dfwhole = dfwhole.append(dfday)
            dfwhole = dfwhole[(dfwhole.snr >= snr) &
                              (dfwhole.significance >= significance)]
            dfwhole = dfwhole.reset_index(drop=True)
        except FileNotFoundError:
            print("Hveto did not run on {0}".format(j))
    print(dfwhole)

    dfwhole.to_csv(filename, index=None)

    return
