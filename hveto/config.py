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

"""The HierarchichalVeto algorithm
"""

try:
    import configparser
except ImportError:  # python 2.x
    import ConfigParser as configparser

from . import version

__version__ = version.version
__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Joshua Smith <joshua.smith@ligo.org>'


class HvetoConfigParser(configparser.ConfigParser):
    HVETO_DEFAULTS = {
       'hveto': {
            'snr-thresholds': (8, 10, 12, 15, 20, 50, 100, 300),
            'time-windows': (.1, .2, .5, 1, 2, 5),
            'minimum-significance': 5,
        },
        'segments': {
            'url': 'https://segments.ligo.org',
            'analysis-flag': '%(IFO)s:DMT-ANALYSIS_READY:1',
            'padding': (0, 0),
        },
        'primary': {
            'channel': '%(IFO)s:GDS-CALIB_STRAIN',
            'trigger-generator': 'Omicron',
            'snr-threshold': 8,
            'frequency-range': (30, 2048),
        },
        'auxiliary': {
            'trigger-generator': 'Omicron',
            'frequency-range': (30, 2048),
        },
        'safety': {
            'unsafe-channels': ['%(IFO)s:GDS-CALIB_STRAIN',
                                '%(IFO)s:LDAS-STRAIN',
                                '%(IFO)s:CAL-DELTAL_EXTERNAL_DQ',
                                '%(IFO)s:DER_DATA_H',
                                '%(IFO)s:h_4096Hz',
                                '%(IFO)s:h_16384Hz'],
        }
    }

    def __init__(self, ifo=None, defaults=dict(), **kwargs):
        if ifo is not None:
           defaults.setdefault('IFO', ifo)
        configparser.ConfigParser.__init__(self, defaults=defaults, **kwargs)
        self.set_hveto_defaults()

    def set_hveto_defaults(self):
        for section in self.HVETO_DEFAULTS:
            self.add_section(section)
            for key, val in self.HVETO_DEFAULTS[section].iteritems():
                if key.endswith('channels') and isinstance(val, (tuple, list)):
                    self.set(section, key, '\n'.join(list(val)))
                elif isinstance(val, tuple):
                    self.set(section, key, ', '.join(map(str, val)))
                else:
                    self.set(section, key, str(val))

    def read(self, filenames):
        readok = configparser.ConfigParser.read(self, filenames)
        for f in filenames:
            if f not in readok:
                raise IOError("Cannot read file %r" % f)
        return readok
    read.__doc__ = configparser.ConfigParser.read.__doc__

    def getfloats(self, section, option):
        return self._get(section, comma_separated_floats, option)


def comma_separated_floats(string):
    return map(float, string.split(','))
