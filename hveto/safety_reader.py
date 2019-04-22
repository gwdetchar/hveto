#!/usr/bin/env python
# vim: nu:ai:ts=4:sw=4

#
#  Copyright (C) 2019 Joseph Areeda <joseph.areeda@ligo.org>
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

"""Safety studies can use a different hdf5 format"""

import h5py

from gwpy.table import EventTable

def safety_h5_read(inpath, grp='/'):
    """Read all events from group as channelx
    INPUT
    =====
    :param inpath: path to the hdf5 file
    :param grp: pathto grou containing trigger dataset(s)

    OUTPUT
    ======
    :return: dict of EventTable for each
    :return: dict of EventTable for each non-empty dataset
    """

    infile = h5py.File(inpath, 'r')
    chans = infile.get(grp)
    ret = dict()

    for chan in chans:
        ev = infile.get(chan)
        if len(ev) > 0:
            evtbl = EventTable(ev[()])
            ret[chan] = evtbl

    return ret
