#!/usr/bin/env python
# vim: nu:ai:ts=4:sw=4

#
#  Copyright (C) 2020 Joseph Areeda <joseph.areeda@ligo.org>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Run at the appropriate site, it takes injection start, duration and
data quality segment file, producing a primary h5 file with just the strain
triggers and an aux h5 file with an hours worth of all channels """

import time

from VOEventLib.VOEvent import Time

start_time = time.time()

__author__ = 'joseph areeda'
__email__ = 'joseph.areeda@ligo.org'
__version__ = '0.0.1'
__process_name__ = 'hveto-saftey-get-trigs'

import argparse
import glob
import h5py
import logging
import os
import re
import socket

import astropy

from gwpy.segments import DataQualityFlag
from gwpy.segments import SegmentList
from gwpy.segments import Segment
from gwpy.table import EventTable
from gwpy.time import to_gps
from gwtrigfind import find_trigger_files


def gps2utc(gps):
    """Convert GPS time to string"""
    gps_time = astropy.time.Time(int(gps), format='gps', scale='utc')
    utc = gps_time.datetime.strftime('%Y-%m-%d %H:%M:%S')
    return utc

def get_events(tcache):
    """Create abreviated event table from cache list"""
    trigs = EventTable.read(tcache, format='ligolw',
                            tablename='sngl_burst',
                            columns=['peak_time', 'peak_time_ns',
                                     'snr', 'peak_frequency',
                                     'amplitude'])
    # grab time, snr and freq of triggers
    time = trigs['peak_time'] + trigs['peak_time_ns'] * 1e-9
    freq = trigs['peak_frequency']
    snr = trigs['snr']

    ret = EventTable()
    ret['time'] = time
    ret['freq'] = freq
    ret['snr'] = snr
    return ret

def plot_tbl(table, channel):
    plot = table.scatter('time', 'freq', color='snr',
                         edgecolor='none')
    ax = plot.gca()

    ax.set_xlim(start, end)
    ax.set_yscale('log')
    ax.set_ylabel('Frequency [Hz]')
    plot.suptitle('Omicron triggers ' + channel)

    plot.add_colorbar(clim=[1, 75], cmap='viridis', log=True,
                      label='Signal-to-noise ratio (SNR)')
    return plot

if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger(__process_name__)
    logger.setLevel(logging.DEBUG)

    start_time = time.time()
    ifo = None

    host = socket.gethostname()
    if 'ligo-wa' in host:
        ifo = 'H1'
    elif 'ligo-la' in host:
        ifo = 'L1'

    parser = argparse.ArgumentParser(description=__doc__,
                                     prog=__process_name__)
    parser.add_argument('-v', '--verbose', action='count', default=1,
                        help='increase verbose output')
    parser.add_argument('-q', '--quiet', default=False, action='store_true',
                        help='show only fatal errors')
    parser.add_argument('-i', '--ifo', required=ifo is None, default=ifo,
                        help='Interferometer (H1, L1), default [{:s}]'.
                        format(ifo if ifo is not None else ''))
    parser.add_argument('-s', '--start', type=to_gps, required=True,
                        help='Starting gps of injections')
    parser.add_argument('-e', '--end', type=to_gps, required=True,
                        help='Ending time or duration')
    parser.add_argument('-S', '--segs', help='segment xml files')
    parser.add_argument('-o', '--outbase',
                        help='path & basename to output files ')

    args = parser.parse_args()

    verbosity = args.verbose

    if verbosity < 1:
        logger.setLevel(logging.CRITICAL)
    elif verbosity < 2:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)

    ifo = args.ifo
    start = args.start
    end = args.end
    if end.gpsSeconds < 1e8:
        end += start

    prim = ifo + ':GDS-CALIB_STRAIN'
    prim_cache = find_trigger_files(prim, 'omicron', start, end)
    prim_trigs = get_events(prim_cache)
    prim_trigs = prim_trigs[(prim_trigs['freq']>15) &
                            (prim_trigs['freq']<900)]
    prim_filename = args.outbase + '-primary.h5'
    with h5py.File(prim_filename, 'w') as prim_out:
        prim_trigs.write(prim_out, path='/'+prim)
    prim_plot = plot_tbl(prim_trigs, prim)
    logger.info('Primary triggers written to {:s}'.format(prim_filename))

    prim_plot_file = args.outbase + '-primary.png'
    prim_plot.savefig(prim_plot_file, edgecolor='white', figsize=[12, 6],
                 dpi=100, bbox_inches='tight')
    logger.info('Primary trig plot written to {:s}'.format(prim_plot_file))

    trig_path = os.path.join('/home/detchar/triggers', ifo)
    trigfiles = glob.glob(trig_path+'/*_OMICRON')

    aux_file = args.outbase + '-auxiliary.h5'
    aux_end = end + 10
    aux_start = aux_end - 3600

    with h5py.File(aux_file, 'w') as aux:
        for path in trigfiles:
            dirname = os.path.basename(path)
            chan = ifo + ':' + dirname.replace('_','-',1).\
                    replace('_OMICRON', '')
            aux_cache = find_trigger_files(chan, 'omicron', aux_start, aux_end)
            if len(aux_cache) > 0:
                aux_trigs = get_events(aux_cache)
                if len(aux_trigs) > 0:
                    aux_trigs.write(aux, path=chan)

    logger.info('Wrote aux triggers to {:s}'.format(aux_file))
    # -------
    elap = time.time() - start_time
    logger.info('Run time {:.1} s'.format(elap))

