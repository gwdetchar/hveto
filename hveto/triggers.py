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

"""Trigger I/O utilities for hveto
"""

import glob
import os.path
import re
import warnings
from collections import OrderedDict

import numpy

from astropy.table import vstack as vstack_tables

import gwtrigfind

from gwpy.io import cache as io_cache
from gwpy.io.utils import file_list
from gwpy.table import EventTable
from gwpy.table.filters import in_segmentlist
from gwpy.table.io.pycbc import filter_empty_files as filter_empty_pycbc_files
from gwpy.segments import SegmentList

# Table metadata keys to keep
TABLE_META = ('tablename',)

DEFAULT_FORMAT = {
    # ETG      format
    "omicron": "hdf5",
    "pycbc_live": "hdf5.pycbc_live",
    "kleinewelle": "ligolw",
    "dmt_omega": "ligolw",
}

DEFAULT_TRIGFIND_OPTIONS = {
    # ETG          format
    ("dmt_omega", "ligolw"): {
        "ext": "xml.gz",
    },
    ("kleinewelle", "ligolw"): {
        "ext": "xml.gz",
    },
    ("omicron", "hdf5"): {
        "ext": "h5",
    },
    ("omicron", "ligolw"): {
        "ext": "xml.gz",
    },
    ("omicron", "root.omicron"): {
        "ext": "root",
    }
}

_SNGL_BURST_OPTIONS = {
    "tablename": "sngl_burst",
    "columns": ["peak", "peak_frequency", "snr"],
    "use_numpy_dtypes": True,
}

DEFAULT_READ_OPTIONS = {
    # ETG          format
    ("dmt_omega", "ligolw"): _SNGL_BURST_OPTIONS,
    ("kleinewelle", "ligolw"): _SNGL_BURST_OPTIONS,
    ("omicron", "ligolw"): _SNGL_BURST_OPTIONS,
    ("omicron", "hdf5"): {
        "path": "triggers",
        "columns": ["time", "frequency", "snr"],
    },
    ("pycbc_live", "hdf5.pycbc_live"): {
        "extended_metadata": False,
        "loudest": True,
        "columns": ["end_time", "template_duration", "new_snr"],
    },
}


# -- find files/channels ------------------------------------------------------

def find_trigger_files(channel, etg, segments, **kwargs):
    """Find trigger files for a given channel and ETG

    Parameters
    ----------
    channel : `str`
        name of channel to find

    etg : `str`
        name of event trigger generator to find

    segments : :class:`~ligo.segments.segmentlist`
        list of segments to find

    **kwargs
        all other keyword arguments are passed to
        `gwtrigfind.find_trigger_urls`

    Returns
    -------
    cache : `list` of `str`
        cache of trigger file paths

    See Also
    --------
    gwtrigfind.find_trigger_urls
        for details on file discovery
    """
    # format arguments
    etg = _sanitize_name(etg)
    try:
        readfmt = kwargs.pop("format", DEFAULT_FORMAT[etg])
    except KeyError:
        raise ValueError("unsupported ETG {!r}".format(etg))
    for key, val in DEFAULT_TRIGFIND_OPTIONS.get((etg, readfmt), {}).items():
        kwargs.setdefault(key, val)

    cache = []
    for start, end in segments:
        try:
            cache.extend(gwtrigfind.find_trigger_files(channel, etg, start,
                                                       end, **kwargs))
        except ValueError as e:
            if str(e).lower().startswith('no channel-level directory'):
                warnings.warn(str(e))
            else:
                raise

    # sanitise URLs (remove 'file://' prefix, etc)
    cache = file_list(cache)

    # remove 'empty' pycbc files from the cache
    if etg == "pycbc_live":
        ifo = channel.split(":", 1)[0]
        cache = filter_empty_pycbc_files(cache, ifo=ifo)

    return type(cache)(OrderedDict.fromkeys(cache))


re_delim = re.compile('[_-]')


def find_auxiliary_channels(etg, gps='*', ifo='*', cache=None):
    """Find all auxiliary channels processed by a given ETG

    If `cache=None` is given (default), the channels are parsed from the
    ETG archive under ``/home/detchar/triggers``. Otherwise, the channel
    names are parsed from the files in the `cache`, assuming they follow
    the T050017 file-naming convention.

    Parameters
    ----------
    etg : `str`
        name of the trigger generator
    gps : `int`, `tuple`, optional
        GPS reference time, or pair of times indicating [start, end),
        at which to find channels
    ifo : `str`, optional
        interferometer prefix for which to find channels
    cache : `list` of `str`, optional
        `list` of files from which to parse channels

    Returns
    -------
    channels : `list` of `str`
        the names of all available auxiliary channels
    """
    out = set()
    if cache is not None:
        for url in cache:
            try:
                ifo, name = os.path.basename(url).split('-')[:2]
            except AttributeError:  # CacheEntry
                ifo = url.observatory
                name = url.description
            channel = '%s:%s' % (ifo, name.replace('_', '-', 1))
            if channel.lower().endswith(etg.lower()):
                channel = channel[:-len(etg)]
            out.add(u'%s' % channel.rstrip('_'))
    else:
        if not isinstance(gps, (list, tuple)):
            gps = (gps, gps)
        gps5 = int(str(gps[0])[:5])
        gpse = int(str(gps[-1])[:5])
        while gps5 <= gpse and gps5 * 1e5 < gps[-1]:
            channels = glob.glob(os.path.join(
                '/home/detchar/triggers', ifo, '*', str(gps5)))
            if len(channels) == 0:  # try old convention
                channels = glob.glob(os.path.join(
                    '/home/detchar/triggers', '*', ifo, '*', str(gps5)))
                use_o2 = False
            else:
                use_o2 = True
            stub = '_%s' % etg.lower()
            for path in channels:
                path = os.path.split(path)[0]
                if not path.lower().endswith('_%s' % etg.lower()):
                    continue
                ifo, name = path[:-len(stub)].rsplit(os.path.sep)[-2:]
                if use_o2:
                    out.add(u'%s:%s' % (ifo, name.replace('_', '-', 1)))
                else:
                    out.add(u'%s:%s' % (ifo, name))
            gps5 += 1
    return sorted(out)


# -- read ---------------------------------------------------------------------


def _sanitize_name(name):
    return re.sub("[-_\.]", "_", name).lower()  # noqa: W605


def _format_params(channel, etg, fmt, trigfind_kwargs, read_kwargs):
    # format kwargs for trigfind
    if trigfind_kwargs is None:
        trigfind_kwargs = {}
    for key, val in DEFAULT_TRIGFIND_OPTIONS.get((etg, fmt), {}).items():
        trigfind_kwargs.setdefault(key, val)

    # format default read kwargs
    for key, val in DEFAULT_READ_OPTIONS.get((etg, fmt), {}).items():
        read_kwargs.setdefault(key, val)
    read_kwargs.setdefault("format", fmt)

    # format params
    for key in read_kwargs:
        if (key.endswith(('columns', 'names', 'branches')) and
                isinstance(read_kwargs[key], str)):
            read_kwargs[key] = [x.strip() for x in read_kwargs[key].split(',')]

    # custom params for ETGs
    if etg == "pycbc_live":
        read_kwargs.setdefault("ifo", channel.split(":", 1)[0])

    return trigfind_kwargs, read_kwargs


def get_triggers(channel, etg, segments, cache=None, snr=None, frange=None,
                 raw=False, trigfind_kwargs={}, **read_kwargs):
    """Get triggers for the given channel
    """
    etg = _sanitize_name(etg)
    # format arguments
    try:
        readfmt = read_kwargs.pop("format", DEFAULT_FORMAT[etg])
    except KeyError:
        raise ValueError("unsupported ETG {!r}".format(etg))
    trigfind_kwargs, read_kwargs = _format_params(
        channel,
        etg,
        readfmt,
        trigfind_kwargs,
        read_kwargs
    )

    # find triggers
    if cache is None:
        cache = find_trigger_files(channel, etg, segments, **trigfind_kwargs)

    # read files
    tables = []
    for segment in segments:
        segaslist = SegmentList([segment])
        segcache = io_cache.sieve(cache, segment=segment)
        # try and work out if cache overextends segment (so we need to crop)
        cachesegs = io_cache.cache_segments(segcache)
        outofbounds = abs(cachesegs - segaslist)
        if segcache:
            if len(segcache) == 1:  # just pass the single filename
                segcache = segcache[0]
            new = EventTable.read(segcache, **read_kwargs)
            new.meta = {k: new.meta[k] for k in TABLE_META if new.meta.get(k)}
            if outofbounds:
                new = new[in_segmentlist(new[new.dtype.names[0]], segaslist)]
            tables.append(new)
    if len(tables):
        table = vstack_tables(tables)
    else:
        table = EventTable(names=read_kwargs.get(
            'columns', ['time', 'frequency', 'snr']))

    # parse time, frequency-like and snr-like column names
    columns = table.dtype.names
    tcolumn = columns[0]
    fcolumn = columns[1]
    scolumn = columns[2]

    # filter
    keep = numpy.ones(len(table), dtype=bool)
    if snr is not None:
        keep &= table[scolumn] >= snr
    if frange is not None:
        keep &= table[fcolumn] >= frange[0]
        keep &= table[fcolumn] < frange[1]
    table = table[keep]

    # return basic table if 'raw'
    if raw:
        return table

    # rename time column so that all tables match in at least that
    if tcolumn != "time":
        table.rename_column(tcolumn, 'time')

    # add channel column to identify all triggers
    table.add_column(table.Column(data=numpy.repeat(channel, len(table)),
                                  name='channel'))

    table.sort('time')
    return table
