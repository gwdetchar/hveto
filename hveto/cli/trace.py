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

"""Check whether a specified trigger time was vetoed by an hveto analysis
"""

import os
import sys
import json

from gwpy.segments import SegmentList

from gwdetchar import cli

from .. import __version__

__author__ = 'Joshua Smith <joshua.smith@ligo.org>'

PROG = ('python -m hveto.cli.trace' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))


# -- parse command line -------------------------------------------------------

def _abs_path(p):
    return os.path.abspath(os.path.expanduser(p))


def create_parser():
    """Create a command-line parser for this entry point
    """
    parser = cli.create_parser(
        prog=PROG,
        description=__doc__,
        version=__version__,
    )
    parser.add_argument(
        '-t',
        '--trigger-time',
        required=True,
        help='GPS time of the trigger',
    )
    parser.add_argument(
        '-d',
        '--directory',
        required=True,
        type=_abs_path,
        help=('path to the hveto output directory containing '
              'a summary-stats.json file'),
    )
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_const',
        dest='loglevel',
        const='DEBUG',
        default='INFO',
        help='Log verbose output',
    )
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the hveto-trace command-line tool
    """
    parser = create_parser()
    args = parser.parse_args(args=args)

    # initialize variables
    time = float(args.trigger_time)
    segment = None

    # initialize logger
    logger = cli.logger(name=PROG.split('python -m ').pop(),
                        level=args.loglevel)
    logger.debug('Running in verbose mode')
    logger.debug('Search directory: {}'.format(args.directory))

    try:  # read veto segment statistics
        segment_stats = json.load(open(os.path.join(
            args.directory, 'summary-stats.json')))
    except IOError:
        logger.critical("'summary-stats.json' was not found "
                        "in the input directory")
        raise

    # loop over and log results to output
    for (i, cround) in enumerate(segment_stats['rounds']):
        seg_files = filter(
            lambda f_name: '.txt' in f_name,
            cround[u'files'][u'VETO_SEGS'])
        for f in seg_files:
            segments = SegmentList.read(os.path.join(args.directory, f))
            if time in segments:
                segment = segments[segments.find(time)]
                logger.info('Trigger time {0} was vetoed in round {1} by '
                            'segment {2}'.format(time, (i + 1), segment))
                logger.debug('Round winner: {}'.format(cround['name']))
                logger.debug('Significance: {}'.format(cround['significance']))
                logger.debug('SNR: {}'.format(cround['snr']))
                logger.debug('Window: {}'.format(cround['window']))

    if segment is None:
        # if we got here, the signal was not vetoed
        logger.info('Trigger time {} was not vetoed'.format(time))


# -- run from command-line ----------------------------------------------------

if __name__ == "__main__":
    main()
