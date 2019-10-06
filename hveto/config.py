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

"""
Configuration files for Hveto
#############################

How to write a configuration file
=================================

The `hveto` command-line executable can run without a configuration file, and
will auto-select the primary channel, and attempt to auto-detect which
auxiliary channels are available. It will also inset a minimal list of 'unsafe'
channels so that the analysis isn't totally meaningless.

However, the way that things are auto-detected means that the resulting output
isn't exactly reproducable after-the-fact in general. If someone adds or
removes data for an auxiliary channel, a rerun will operate over a different
channel lists, and confusion will reign.

So, it is highly recommended that you use a custom configuration file for your
analyses. It could be that the configuration file never changes, but the very
fact that it exists should mean that you are in much greater control over what
the output will look like.

Each of the below sections lists the valid options and a description of what
the value should be, and then an example of what that section might look like
in the INI format:

[hveto]
-------

========================  =====================================================
``snr-thresholds``        A comma-separated list of signal-to-noise ratio
                          thresholds over which to test each auxiliary channel
``time-windows``          A comma-separated list of time windows (in
                          seconds) over which to test each auxiliary channel
``minimum-significance``  The significance value below which to stop the
                          analysis
========================  =====================================================

.. code-block:: ini

   [hveto]
   ; comma-separated list of SNR thresholds (pass >=)
   snr-thresholds = 7.75, 8, 8.5, 9, 10, 11, 12, 15, 20, 40, 100, 300
   ; comma-separated list of time windows
   time-windows = .1, .2, .4, .8, 1
   minimum-significance = 5

[primary]
---------

=====================  ========================================================
``channel``            The name of the primary channel
``trigger-generator``  The name of the primary trigger generator
``snr-threshold``      The minimum threshold on signal-to-noise ratio for
                       primary channel events to be included in the analysis
``frequency-range``    The `(low, high`) frequency range of interest for this
                       analysis. Note that for CBC trigger generators, the
                       ``'template_duration'`` column is used here.
``read-format``        The ``format`` name to use when reading files for this
                       trigger generator
``read-columns``       The list of three column names equivalent to
                       `time-like,frequency-like,snr-like` for this trigger
                       generator
=====================  ========================================================

.. code-block:: ini

   [primary]
   ; use Omicron calibrated strain as primary
   channel = %(IFO)s:GDS-CALIB_STRAIN
   trigger-generator = omicron
   ; SNR threshold (pass >=)
   snr-threshold = 6
   ; flow, fhigh
   frequency-range = 0, 2048.
   ; format
   read-format = ligolw
   read-tablename = sngl_burst
   ; read-columns to read
   read-columns = peak, peak_frequency, snr

.. note::

   In this section the ``%(IFO)s`` interpolation variable has been used. This
   can be used throughout the configuration so that you only have to write one
   for all interferometers, with the correct two-character prefix being
   inserted automatically at run time.

.. note::

   As well as the above, users can specify arguments to be used when
   automatically discovering triggers. Any option that begins ``trigfind-``
   will be passed to the `trigfind.find_trigger_urls` function as a keyword
   argument.

   Specifically, to specify the specific run associated with the ``daily-cbc``
   event generator, you can give

   .. code-block:: ini

      [primary]
      trigger-generator = daily-cbc
      trigfind-run = bbh_gds
      trigfind-filetag = 16SEC_CLUSTERED
      read-format = ligolw
      read-tablename = sngl_inspiral
      read-columns = end,template_duration,snr

[auxiliary]
-----------

=====================  ========================================================
``trigger-generator``  The name of the auxiliary trigger generator
``frequency-range``    The `(low, high)` frequency range of interest
``read-format``        The ``format`` name to use when reading files for this
                       trigger generator
``read-columns``       The list of three column names equivalent to
                       `time-like,frequency-like,snr-like` for this trigger
                       generator
``channels``           a tab-indented, line-delimited list of auxiliary channel
                       names
=====================  ========================================================

.. code-block:: ini

   [auxiliary]
   trigger-generator = omicron
   ; flow, fhigh
   frequency-range = 0, 2048
   ; file format
   read-format = ligolw
   read-tablename = sngl_burst
   ; read-columns to read
   read-columns = peak, peak_frequency, snr
   ; give tab-indented, line-separated list of channels
   channels =
       %(IFO)s:ASC-AS_B_RF45_I_PIT_OUT_DQ
       %(IFO)s:ASC-AS_A_RF45_Q_PIT_OUT_DQ
       %(IFO)s:ASC-X_TR_B_NSUM_OUT_DQ
       %(IFO)s:ISI-ITMX_ST2_BLND_X_GS13_CUR_IN1_DQ
       %(IFO)s:ASC-REFL_A_RF9_I_YAW_OUT_DQ
       %(IFO)s:ASC-AS_A_RF45_Q_YAW_OUT_DQ

.. note::

   As with the ``[primary]`` section, users can specify ``trigfind-``
   arguments to customise trigger-file discovery.

[segments]
----------

===========================  ==================================================
``url``                      The URL of the segment database
``analysis-flag``            The name of the data-quality flag indicating
                             analysable times
``padding``                  The `(pre, post)` padding to apply to the analysis
                             segments [note both `pre` and `post` operate
                             forward in time, so to pad out at the start of a
                             segment (or in at the end), use a negative number]
``veto-definer-file``        The path of a veto-definer file to apply before
                             analysis (can be a remote URL)
``veto-definer-categories``  Comma-separated list of category integers to
                             apply, defaults to all flags in veto-definer file
===========================  ==================================================

.. code-block:: ini

   [segments]
   url = https://segments.ligo.org
   ; require full observation mode
   analysis-flag = %(IFO)s:DMT-ANALYSIS_READY:1
   ; no padding by default
   padding = 0, 0

[safety]
--------

===================  ==========================================================
``unsafe-channels``  The list of unsafe channels (tab-indented, line-delimited)
===================  ==========================================================

.. code-block:: ini

   [safety]
   unsafe-channels =
       %(IFO)s:GDS-CALIB_STRAIN
       %(IFO)s:CAL-DELTAL_EXTERNAL_DQ
       %(IFO)s:OAF-CAL_DARM_DQ
       %(IFO)s:OMC-DCPD_SUM_OUT_DQ

Module API
==========
"""

import configparser

from .segments import DEFAULT_SEGMENT_SERVER

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
            'url': DEFAULT_SEGMENT_SERVER,
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
        },
    }

    def __init__(self, ifo=None, defaults=dict(), **kwargs):
        if ifo is not None:
            defaults.setdefault('IFO', ifo)
        configparser.ConfigParser.__init__(self, defaults=defaults, **kwargs)
        self.set_hveto_defaults()

    def set_hveto_defaults(self):
        for section in self.HVETO_DEFAULTS:
            self.add_section(section)
            for key, val in self.HVETO_DEFAULTS[section].items():
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

    def getparams(self, section, prefix):
        nchar = len(prefix)
        params = dict((key[nchar:], val) for (key, val) in
                      self.items(section) if key.startswith(prefix))
        # try simple typecasting
        for key in params:
            if params[key].lower() in ('true', 'false'):
                params[key] = bool(params[key])
            else:
                try:
                    params[key] = float(params[key])
                except ValueError:
                    pass
        return params


def comma_separated_floats(string):
    return tuple(map(float, string.split(',')))
