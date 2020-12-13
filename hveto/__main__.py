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

"""Run the HierarchichalVeto (hveto) algorithm over some data
"""

import configparser
import datetime
import json
import multiprocessing
import numpy
import os
import random
import sys
import time
import warnings

from getpass import getuser
from pathlib import Path
from socket import getfqdn

from gwpy.io.cache import read_cache
from gwpy.segments import (Segment, SegmentList,
                           DataQualityFlag, DataQualityDict)

from gwdetchar import cli
from gwdetchar.io.html import (FancyPlot, cis_link)
from gwdetchar.omega import batch

from hveto import (__version__, config, core, html, utils)
from hveto.segments import (write_ascii as write_ascii_segments,
                            read_veto_definer_file)
from hveto.triggers import (get_triggers, find_auxiliary_channels)

# set matplotlib backend
from matplotlib import use
use("Agg")

# backend-dependent imports
from gwdetchar.plot import texify  # noqa: E402
from hveto import plot  # noqa: E402

IFO = os.getenv('IFO')
JOBSTART = time.time()

# set up logger
PROG = ('python -m hveto' if sys.argv[0].endswith('.py')
        else os.path.basename(sys.argv[0]))
LOGGER = cli.logger(name=PROG.split('python -m ').pop())

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = ('Joshua Smith <joshua.smith@ligo.org>, '
               'Alex Urban <alexander.urban@ligo.org>')


# -- parse command line -------------------------------------------------------

def _abs_path(p):
    return os.path.abspath(os.path.expanduser(p))


def _find_max_significance(channels):
    """Utility to find hveto maximum significance with multiprocessing
    """
    aux = dict((c, auxiliary[c]) for c in channels)
    return core.find_max_significance(primary, aux, pchannel,
                                      snrs, windows, livetime)


def _get_aux_triggers(channel):
    """Retrieve triggers for auxiliary channels
    """
    if acache is None:
        auxcache = None
    else:
        ifo, name = channel.split(':')
        match = "{}-{}".format(ifo, name.replace('-', '_'))
        auxcache = [e for e in acache if Path(e).name.startswith(match)]
    # get triggers
    try:
        trigs = get_triggers(channel, auxetg, analysis.active, snr=minsnr,
                             frange=auxfreq, cache=auxcache, nproc=1,
                             trigfind_kwargs=atrigfindkw, **areadkw)
    # catch error and continue
    except ValueError as e:
        warnings.warn('%s: %s' % (type(e).__name__, str(e)))
        out = None
    else:
        out = (channel, trigs)
    # log result of load
    with counter.get_lock():
        counter.value += 1
        tag = '[%d/%d]' % (counter.value, naux)
        if out is None:  # something went wrong
            LOGGER.critical("    %s Failed to read events for %s"
                            % (tag, channel))
        elif len(trigs):  # no triggers
            LOGGER.debug("    %s Read %d events for %s"
                         % (tag, len(trigs), channel))
        else:  # everything is fine
            LOGGER.warning("    %s No events found for %s"
                           % (tag, channel))
    return out


def _veto(channels):
    """Utility to apply vetoes with multiprocessing
    """
    chandict = dict((c, auxiliary[c]) for c in channels)
    return core.veto_all(chandict, rnd.vetoes)


def create_parser():
    """Create a command-line parser for this entry point
    """
    parser = cli.create_parser(
        prog=PROG,
        description=__doc__,
        version=__version__,
    )

    # gwdetchar standard arguments/options
    cli.add_gps_start_stop_arguments(parser)
    cli.add_ifo_option(parser, required=IFO is None, ifo=IFO)
    cli.add_nproc_option(parser, default=1)

    # custom options
    parser.add_argument(
        '-f',
        '--config-file',
        action='append',
        default=[],
        type=_abs_path,
        help=('path to hveto configuration file, can be given '
              'multiple times (files read in order)'),
    )
    parser.add_argument(
        '-p',
        '--primary-cache',
        default=None,
        type=_abs_path,
        help='path for cache containing primary channel files',
    )
    parser.add_argument(
        '-a',
        '--auxiliary-cache',
        default=None,
        type=_abs_path,
        help=('path for cache containing auxiliary channel files, '
              'files contained must be T050017-compliant with the '
              'channel name as the leading name parts, e.g. '
              '\'L1-GDS_CALIB_STRAIN_<tag>-<start>-<duration>.'
              '<ext>\' for L1:GDS-CALIB_STRAIN triggers'),
    )
    parser.add_argument(
        '-S',
        '--analysis-segments',
        action='append',
        default=[],
        type=_abs_path,
        help=('path to file containing segments for '
              'the analysis flag (name in data file '
              'must match analysis-flag in config file)'),
    )
    parser.add_argument(
        '-w',
        '--omega-scans',
        type=int,
        metavar='NSCAN',
        help=('generate a workflow of omega scans for each round, '
              'this will launch automatically to condor, '
              'requires the gwdetchar package'),
    )

    # output options
    pout = parser.add_argument_group('Output options')
    pout.add_argument(
        '-o',
        '--output-directory',
        default=os.curdir,
        help='path of output directory, default: %(default)s',
    )

    # return the parser
    return parser


# -- main code block ----------------------------------------------------------

def main(args=None):
    """Run the hveto command-line interface
    """
    # declare global variables
    # this is needed for multiprocessing utilities
    global acache, analysis, areadkw, atrigfindkw, auxiliary, auxetg
    global auxfreq, counter, livetime, minsnr, naux, pchannel, primary
    global rnd, snrs, windows

    # parse command-line
    parser = create_parser()
    args = parser.parse_args(args=args)
    ifo = args.ifo
    start = int(args.gpsstart)
    end = int(args.gpsend)
    duration = end - start

    # log startup
    LOGGER.info("-- Welcome to Hveto --")
    LOGGER.info("GPS start time: %d" % start)
    LOGGER.info("GPS end time: %d" % end)
    LOGGER.info("Interferometer: %s" % ifo)

    # -- initialisation -------------------------

    # read configuration
    cp = config.HvetoConfigParser(ifo=ifo)
    cp.read(args.config_file)
    LOGGER.info("Parsed configuration file(s)")

    # format output directory
    outdir = _abs_path(args.output_directory)
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    os.chdir(outdir)
    LOGGER.info("Working directory: %s" % outdir)
    segdir = 'segments'
    plotdir = 'plots'
    trigdir = 'triggers'
    omegadir = 'scans'
    for d in [segdir, plotdir, trigdir, omegadir]:
        if not os.path.isdir(d):
            os.makedirs(d)

    # prepare html variables
    htmlv = {
        'title': '%s Hveto | %d-%d' % (ifo, start, end),
        'config': None,
        'prog': PROG,
        'context': ifo.lower(),
    }

    # get segments
    aflag = cp.get('segments', 'analysis-flag')
    url = cp.get('segments', 'url')
    padding = tuple(cp.getfloats('segments', 'padding'))
    if args.analysis_segments:
        segs_ = DataQualityDict.read(args.analysis_segments, gpstype=float)
        analysis = segs_[aflag]
        span = SegmentList([Segment(start, end)])
        analysis.active &= span
        analysis.known &= span
        analysis.coalesce()
        LOGGER.debug("Segments read from disk")
    else:
        analysis = DataQualityFlag.query(aflag, start, end, url=url)
        LOGGER.debug("Segments recovered from %s" % url)
    if padding != (0, 0):
        mindur = padding[0] - padding[1]
        analysis.active = type(analysis.active)([s for s in analysis.active if
                                                 abs(s) >= mindur])
        analysis.pad(*padding, inplace=True)
        LOGGER.debug("Padding %s applied" % str(padding))
    livetime = int(abs(analysis.active))
    livetimepc = livetime / duration * 100.
    LOGGER.info("Retrieved %d segments for %s with %ss (%.2f%%) livetime"
                % (len(analysis.active), aflag, livetime, livetimepc))

    # apply vetoes from veto-definer file
    try:
        vetofile = cp.get('segments', 'veto-definer-file')
    except configparser.NoOptionError:
        vetofile = None
    else:
        try:
            categories = cp.getfloats('segments', 'veto-definer-categories')
        except configparser.NoOptionError:
            categories = None
        # read file
        vdf = read_veto_definer_file(vetofile, start=start, end=end, ifo=ifo)
        LOGGER.debug("Read veto-definer file from %s" % vetofile)
        # get vetoes from segdb
        vdf.populate(source=url, segments=analysis.active, on_error='warn')
        # coalesce flags from chosen categories
        vetoes = DataQualityFlag('%s:VDF-VETOES:1' % ifo)
        nflags = 0
        for flag in vdf:
            if not categories or vdf[flag].category in categories:
                vetoes += vdf[flag]
                nflags += 1
        try:
            deadtime = int(abs(vetoes.active)) / int(abs(vetoes.known)) * 100
        except ZeroDivisionError:
            deadtime = 0
        LOGGER.debug("Coalesced %ss (%.2f%%) of deadtime from %d veto flags"
                     % (abs(vetoes.active), deadtime, nflags))
        # apply to analysis segments
        analysis -= vetoes
        LOGGER.debug("Applied vetoes from veto-definer file")
        livetime = int(abs(analysis.active))
        livetimepc = livetime / duration * 100.
        LOGGER.info("%ss (%.2f%%) livetime remaining after vetoes"
                    % (livetime, livetimepc))

    snrs = cp.getfloats('hveto', 'snr-thresholds')
    minsnr = min(snrs)
    windows = cp.getfloats('hveto', 'time-windows')

    # record all segments
    segments = DataQualityDict()
    segments[analysis.name] = analysis

    # -- load channels --------------------------

    # get primary channel name
    pchannel = cp.get('primary', 'channel')

    # read auxiliary cache
    if args.auxiliary_cache is not None:
        acache = read_cache(args.auxiliary_cache)
    else:
        acache = None

    # load auxiliary channels
    auxetg = cp.get('auxiliary', 'trigger-generator')
    auxfreq = cp.getfloats('auxiliary', 'frequency-range')
    try:
        auxchannels = cp.get('auxiliary', 'channels').strip('\n').split('\n')
    except config.configparser.NoOptionError:
        auxchannels = find_auxiliary_channels(auxetg, (start, end), ifo=ifo,
                                              cache=acache)
        cp.set('auxiliary', 'channels', '\n'.join(auxchannels))
        LOGGER.debug("Auto-discovered %d "
                     "auxiliary channels" % len(auxchannels))
    else:
        auxchannels = sorted(set(auxchannels))
        LOGGER.debug("Read list of %d auxiliary channels" % len(auxchannels))

    # load unsafe channels list
    _unsafe = cp.get('safety', 'unsafe-channels')
    if os.path.isfile(_unsafe):  # from file
        unsafe = set()
        with open(_unsafe, 'rb') as f:
            for c in f.read().rstrip('\n').split('\n'):
                if c.startswith('%(IFO)s'):
                    unsafe.add(c.replace('%(IFO)s', ifo))
                elif not c.startswith('%s:' % ifo):
                    unsafe.add('%s:%s' % (ifo, c))
                else:
                    unsafe.add(c)
    else:  # or from line-seprated list
        unsafe = set(_unsafe.strip('\n').split('\n'))
    unsafe.add(pchannel)
    cp.set('safety', 'unsafe-channels', '\n'.join(sorted(unsafe)))
    LOGGER.debug("Read list of %d unsafe channels" % len(unsafe))

    # remove unsafe channels
    nunsafe = 0
    for i in range(len(auxchannels) - 1, -1, -1):
        if auxchannels[i] in unsafe:
            LOGGER.warning("Auxiliary channel %r identified as unsafe and has "
                           "been removed" % auxchannels[i])
            auxchannels.pop(i)
            nunsafe += 1
    LOGGER.debug("%d auxiliary channels identified as unsafe" % nunsafe)
    naux = len(auxchannels)
    LOGGER.info("Identified %d auxiliary channels to process" % naux)

    # record INI file in output HTML directory
    inifile = '%s-HVETO_CONFIGURATION-%d-%d.ini' % (ifo, start, duration)
    if os.path.isfile(inifile) and any(
            os.path.samefile(inifile, x) for x in args.config_file):
        LOGGER.debug("Cannot write INI file to %s, file was given as input")
    else:
        with open(inifile, 'w') as f:
            cp.write(f)
        LOGGER.info("Configuration recorded as %s" % inifile)
    htmlv['config'] = inifile

    # -- load primary triggers ------------------

    # read primary cache
    if args.primary_cache is not None:
        pcache = read_cache(args.primary_cache)
    else:
        pcache = None

    # load primary triggers
    petg = cp.get('primary', 'trigger-generator')
    psnr = cp.getfloat('primary', 'snr-threshold')
    pfreq = cp.getfloats('primary', 'frequency-range')
    preadkw = cp.getparams('primary', 'read-')
    if pcache is not None:  # auto-detect the file format
        LOGGER.debug('Unsetting the primary trigger file format')
        preadkw['format'] = None
        preadkw['path'] = 'triggers'
    ptrigfindkw = cp.getparams('primary', 'trigfind-')
    primary = get_triggers(pchannel, petg, analysis.active, snr=psnr,
                           frange=pfreq, cache=pcache, nproc=args.nproc,
                           trigfind_kwargs=ptrigfindkw, **preadkw)
    fcol, scol = primary.dtype.names[1:3]

    if len(primary):
        LOGGER.info("Read %d events for %s" % (len(primary), pchannel))
    else:
        message = "No events found for %r in %d seconds of livetime" % (
           pchannel, livetime)
        LOGGER.critical(message)

    # cluster primary triggers
    clusterkwargs = cp.getparams('primary', 'cluster-')
    if clusterkwargs:
        primary = primary.cluster(**clusterkwargs)
        LOGGER.info("%d primary events remain after clustering over %s" %
                    (len(primary), clusterkwargs['rank']))

    # -- bail out early -------------------------
    # the bail out is done here so that we can at least generate the eventual
    # configuration file, mainly for HTML purposes

    # no segments
    if livetime == 0:
        message = ("No active segments found for analysis flag %r in interval "
                   "[%d, %d)" % (aflag, start, end))
        LOGGER.critical(message)
        htmlv['context'] = 'info'
        index = html.write_null_page(ifo, start, end, message, **htmlv)
        LOGGER.info("HTML report written to %s" % index)
        sys.exit(0)

    # no primary triggers
    if len(primary) == 0:
        htmlv['context'] = 'danger'
        index = html.write_null_page(ifo, start, end, message, **htmlv)
        LOGGER.info("HTML report written to %s" % index)
        sys.exit(0)

    # otherwise write all primary triggers to ASCII
    trigfile = os.path.join(
        trigdir,
        '%s-HVETO_RAW_TRIGS_ROUND_0-%d-%d.txt' % (ifo, start, duration),
    )
    primary.write(trigfile, format='ascii', overwrite=True)

    # -- load auxiliary triggers ----------------

    LOGGER.info("Reading triggers for aux channels...")
    counter = multiprocessing.Value('i', 0)

    areadkw = cp.getparams('auxiliary', 'read-')
    if acache is not None:  # auto-detect the file format
        LOGGER.debug('Unsetting the auxiliary trigger file format')
        areadkw['format'] = None
        areadkw['path'] = 'triggers'
    atrigfindkw = cp.getparams('auxiliary', 'trigfind-')

    # map with multiprocessing
    if args.nproc > 1:
        pool = multiprocessing.Pool(processes=args.nproc)
        results = pool.map(_get_aux_triggers, auxchannels)
        pool.close()
    # map without multiprocessing
    else:
        results = map(_get_aux_triggers, auxchannels)

    LOGGER.info("All aux events loaded")

    auxiliary = dict(x for x in results if x is not None)
    auxchannels = sorted(auxiliary.keys())
    chanfile = '%s-HVETO_CHANNEL_LIST-%d-%d.txt' % (ifo, start, duration)
    with open(chanfile, 'w') as f:
        for chan in auxchannels:
            print(chan, file=f)
    LOGGER.info("Recorded list of valid auxiliary channels in %s" % chanfile)

    # -- execute hveto analysis -----------------

    minsig = cp.getfloat('hveto', 'minimum-significance')

    pevents = [primary]
    pvetoed = []

    auxfcol, auxscol = auxiliary[auxchannels[0]].dtype.names[1:3]
    slabel = plot.get_column_label(scol)
    flabel = plot.get_column_label(fcol)
    auxslabel = plot.get_column_label(auxscol)
    auxflabel = plot.get_column_label(auxfcol)

    rounds = []
    rnd = core.HvetoRound(1, pchannel, rank=scol)
    rnd.segments = analysis.active

    while True:
        LOGGER.info("-- Processing round %d --" % rnd.n)

        # write segments for this round
        segfile = os.path.join(
            segdir, '%s-HVETO_ANALYSIS_SEGS_ROUND_%d-%d-%d.txt'
                    % (ifo, rnd.n, start, duration))
        write_ascii_segments(segfile, rnd.segments)

        # calculate significances for this round
        if args.nproc > 1:  # multiprocessing
            # separate channel list into chunks and process each chunk
            pool = multiprocessing.Pool(
                processes=min(args.nproc, len(auxiliary.keys())))
            chunks = utils.channel_groups(list(auxiliary.keys()), args.nproc)
            results = pool.map(_find_max_significance, chunks)
            pool.close()
            winners, sigsets = zip(*results)
            # find winner of chunk winners
            winner = sorted(winners, key=lambda w: w.significance)[-1]
            # flatten sets of significances into one list
            newsignificances = sigsets[0]
            for subdict in sigsets[1:]:
                newsignificances.update(subdict)
        else:  # single process
            winner, newsignificances = core.find_max_significance(
                primary, auxiliary, pchannel, snrs, windows, rnd.livetime)

        LOGGER.info("Round %d winner: %s" % (rnd.n, winner.name))

        # plot significance drop here for the last round
        #   only now do we actually have the new data to
        #   calculate significance drop
        if rnd.n > 1:
            svg = (pngname % 'SIG_DROP').replace('.png', '.svg')  # noqa: F821
            plot.significance_drop(
                svg, oldsignificances, newsignificances,  # noqa: F821
                title=' | '.join([title, subtitle]),  # noqa: F821
                bbox_inches='tight')
            LOGGER.debug("Figure written to %s" % svg)
            svg = FancyPlot(svg, caption=plot.ROUND_CAPTION['SIG_DROP'])
            rounds[-1].plots.append(svg)
        oldsignificances = newsignificances  # noqa: F841

        # break out of the loop if the significance is below stopping point
        if winner.significance < minsig:
            LOGGER.info("Maximum signifiance below stopping point")
            LOGGER.debug("    (%.2f < %.2f)" % (winner.significance, minsig))
            LOGGER.info("-- Rounds complete! --")
            break

        # work out the vetoes for this round
        allaux = auxiliary[winner.name][
            auxiliary[winner.name][auxscol] >= winner.snr]
        winner.events = allaux
        coincs = allaux[core.find_coincidences(allaux['time'], primary['time'],
                                               dt=winner.window)]
        rnd.vetoes = winner.get_segments(allaux['time'])
        flag = DataQualityFlag(
            '%s:HVT-ROUND_%d:1' % (ifo, rnd.n), active=rnd.vetoes,
            known=rnd.segments,
            description="winner=%s, window=%s, snr=%s" % (
                winner.name, winner.window, winner.snr))
        segments[flag.name] = flag
        LOGGER.debug("Generated veto segments for round %d" % rnd.n)

        # link events before veto for plotting
        before = primary
        beforeaux = auxiliary[winner.name]

        # apply vetoes to primary
        primary, vetoed = core.veto(primary, rnd.vetoes)
        pevents.append(primary)
        pvetoed.append(vetoed)
        LOGGER.debug("Applied vetoes to primary")

        # record results
        rnd.winner = winner
        rnd.efficiency = (len(vetoed), len(primary) + len(vetoed))
        rnd.use_percentage = (len(coincs), len(winner.events))
        if rnd.n > 1:
            rnd.cum_efficiency = (
                len(vetoed) + rounds[-1].cum_efficiency[0],
                rounds[0].efficiency[1])
            rnd.cum_deadtime = (
                rnd.deadtime[0] + rounds[-1].cum_deadtime[0],
                livetime)
        else:
            rnd.cum_efficiency = rnd.efficiency
            rnd.cum_deadtime = rnd.deadtime

        # apply vetoes to auxiliary
        if args.nproc > 1:  # multiprocess
            # separate channel list into chunks and process each chunk
            pool = multiprocessing.Pool(
                processes=min(args.nproc, len(auxiliary.keys())))
            chunks = utils.channel_groups(list(auxiliary.keys()), args.nproc)
            results = pool.map(_veto, chunks)
            pool.close()
            auxiliary = results[0]
            for subdict in results[1:]:
                auxiliary.update(subdict)
        else:  # single process
            auxiliary = core.veto_all(auxiliary, rnd.vetoes)
        LOGGER.debug("Applied vetoes to auxiliary channels")

        # log results
        LOGGER.info("""Results for round %d:\n\n
    winner :          %s
    significance :    %s
    mu :              %s
    snr :             %s
    dt :              %s
    use_percentage :  %s
    efficiency :      %s
    deadtime :        %s
    cum. efficiency : %s
    cum. deadtime :   %s\n\n""" % (
            rnd.n, rnd.winner.name, rnd.winner.significance,
            rnd.winner.mu, rnd.winner.snr, rnd.winner.window,
            rnd.use_percentage, rnd.efficiency, rnd.deadtime,
            rnd.cum_efficiency, rnd.cum_deadtime))

        # write segments
        segfile = os.path.join(
            segdir,
            '%s-HVETO_VETO_SEGS_ROUND_%d-%d-%d.txt' % (
                ifo, rnd.n, start, duration))
        write_ascii_segments(segfile, rnd.vetoes)
        LOGGER.debug("Round %d vetoes written to %s" % (rnd.n, segfile))
        rnd.files['VETO_SEGS'] = (segfile,)
        # write triggers
        trigfile = os.path.join(
            trigdir,
            '%s-HVETO_%%s_TRIGS_ROUND_%d-%d-%d.txt' % (
                ifo, rnd.n, start, duration))
        for tag, arr in zip(
                ['WINNER', 'VETOED', 'RAW'],
                [winner.events, vetoed, primary]):
            f = trigfile % tag
            arr.write(f, format='ascii', overwrite=True)
            LOGGER.debug("Round %d %s events written to %s"
                         % (rnd.n, tag.lower(), f))
            rnd.files[tag] = f

        # record times to omega scan
        if args.omega_scans:
            N = len(vetoed)
            ind = random.sample(range(0, N), min(args.omega_scans, N))
            rnd.scans = vetoed[ind]
            LOGGER.debug("Collected %d events to omega scan:\n\n%s\n\n"
                         % (len(rnd.scans), rnd.scans))

        # -- make some plots --

        pngname = os.path.join(plotdir, '%s-HVETO_%%s_ROUND_%d-%d-%d.png' % (
            ifo, rnd.n, start, duration))
        wname = texify(rnd.winner.name)
        beforel = 'Before\n[%d]' % len(before)
        afterl = 'After\n[%d]' % len(primary)
        vetoedl = 'Vetoed\n(primary)\n[%d]' % len(vetoed)
        beforeauxl = 'All\n[%d]' % len(beforeaux)
        usedl = 'Used\n(aux)\n[%d]' % len(winner.events)
        coincl = 'Coinc.\n[%d]' % len(coincs)
        title = '%s Hveto round %d' % (ifo, rnd.n)
        ptitle = '%s: primary impact' % title
        atitle = '%s: auxiliary use' % title
        subtitle = 'winner: %s [%d-%d]' % (wname, start, end)

        # before/after histogram
        png = pngname % 'HISTOGRAM'
        plot.before_after_histogram(
            png, before[scol], primary[scol],
            label1=beforel, label2=afterl, xlabel=slabel,
            title=ptitle, subtitle=subtitle)
        LOGGER.debug("Figure written to %s" % png)
        png = FancyPlot(png, caption=plot.ROUND_CAPTION['HISTOGRAM'])
        rnd.plots.append(png)

        # snr versus time
        png = pngname % 'SNR_TIME'
        plot.veto_scatter(
            png, before, vetoed, x='time', y=scol, label1=beforel,
            label2=vetoedl, epoch=start, xlim=[start, end], ylabel=slabel,
            title=ptitle, subtitle=subtitle, legend_title="Primary:")
        LOGGER.debug("Figure written to %s" % png)
        png = FancyPlot(png, caption=plot.ROUND_CAPTION['SNR_TIME'])
        rnd.plots.append(png)

        # snr versus frequency
        png = pngname % 'SNR_%s' % fcol.upper()
        plot.veto_scatter(
            png, before, vetoed, x=fcol, y=scol, label1=beforel,
            label2=vetoedl, xlabel=flabel, ylabel=slabel, xlim=pfreq,
            title=ptitle, subtitle=subtitle, legend_title="Primary:")
        LOGGER.debug("Figure written to %s" % png)
        png = FancyPlot(png, caption=plot.ROUND_CAPTION['SNR'])
        rnd.plots.append(png)

        # frequency versus time coloured by SNR
        png = pngname % '%s_TIME' % fcol.upper()
        plot.veto_scatter(
            png, before, vetoed, x='time', y=fcol, color=scol,
            label1=None, label2=None, ylabel=flabel,
            clabel=slabel, clim=[3, 100], cmap='YlGnBu',
            epoch=start, xlim=[start, end], ylim=pfreq,
            title=ptitle, subtitle=subtitle)
        LOGGER.debug("Figure written to %s" % png)
        png = FancyPlot(png, caption=plot.ROUND_CAPTION['TIME'])
        rnd.plots.append(png)

        # aux used versus frequency
        png = pngname % 'USED_SNR_TIME'
        plot.veto_scatter(
            png, winner.events, vetoed, x='time', y=[auxscol, scol],
            label1=usedl, label2=vetoedl, ylabel=slabel, epoch=start,
            xlim=[start, end], title=atitle, subtitle=subtitle)
        LOGGER.debug("Figure written to %s" % png)
        png = FancyPlot(png, caption=plot.ROUND_CAPTION['USED_SNR_TIME'])
        rnd.plots.append(png)

        # snr versus time
        png = pngname % 'AUX_SNR_TIME'
        plot.veto_scatter(
            png, beforeaux, (winner.events, coincs), x='time', y=auxscol,
            label1=beforeauxl, label2=(usedl, coincl), epoch=start,
            xlim=[start, end], ylabel=auxslabel, title=atitle,
            subtitle=subtitle)
        LOGGER.debug("Figure written to %s" % png)
        png = FancyPlot(png, caption=plot.ROUND_CAPTION['AUX_SNR_TIME'])
        rnd.plots.append(png)

        # snr versus frequency
        png = pngname % 'AUX_SNR_FREQUENCY'
        plot.veto_scatter(
            png, beforeaux, (winner.events, coincs), x=auxfcol, y=auxscol,
            label1=beforeauxl, label2=(usedl, coincl), xlabel=auxflabel,
            ylabel=auxslabel, title=atitle, subtitle=subtitle,
            legend_title="Aux:")
        LOGGER.debug("Figure written to %s" % png)
        png = FancyPlot(png, caption=plot.ROUND_CAPTION['AUX_SNR_FREQUENCY'])
        rnd.plots.append(png)

        # frequency versus time coloured by SNR
        png = pngname % 'AUX_FREQUENCY_TIME'
        plot.veto_scatter(
            png, beforeaux, (winner.events, coincs), x='time', y=auxfcol,
            color=auxscol, label1=None, label2=[None, None], ylabel=auxflabel,
            clabel=auxslabel, clim=[3, 100], cmap='YlGnBu', epoch=start,
            xlim=[start, end], title=atitle, subtitle=subtitle)
        LOGGER.debug("Figure written to %s" % png)
        png = FancyPlot(png, caption=plot.ROUND_CAPTION['AUX_FREQUENCY_TIME'])
        rnd.plots.append(png)

        # move to the next round
        rounds.append(rnd)
        rnd = core.HvetoRound(rnd.n + 1, pchannel, rank=scol,
                              segments=rnd.segments-rnd.vetoes)

    # write file with all segments
    segfile = os.path.join(
        segdir, '%s-HVETO_SEGMENTS-%d-%d.h5' % (ifo, start, duration))
    segments.write(segfile, overwrite=True)
    LOGGER.debug("Segment summary written to %s" % segfile)

    LOGGER.debug("Making summary figures...")

    # -- exit early if no rounds above threshold

    if not rounds:
        message = ("No rounds completed above threshold. Analysis stopped "
                   "with %s achieving significance of %.2f"
                   % (winner.name, winner.significance))
        LOGGER.critical(message)
        message = message.replace(
            winner.name, cis_link(winner.name, class_='alert-link'))
        message += '<br>[T<sub>win</sub>: %ss, SNR: %s]' % (
            winner.window, winner.snr)
        htmlv['context'] = 'warning'
        index = html.write_null_page(ifo, start, end, message, **htmlv)
        LOGGER.info("HTML report written to %s" % index)
        sys.exit(0)

    # -- plot all rounds impact
    pngname = os.path.join(plotdir, '%s-HVETO_%%s_ALL_ROUNDS-%d-%d.png' % (
        ifo, start, duration))
    plots = []
    title = '%s Hveto all rounds' % args.ifo
    subtitle = '%d rounds | %d-%d' % (len(rounds), start, end)

    # before/after histogram
    png = pngname % 'HISTOGRAM'
    beforel = 'Before analysis [%d events]' % len(pevents[0])
    afterl = 'After %d rounds [%d]' % (len(pevents) - 1, len(pevents[-1]))
    plot.before_after_histogram(
        png, pevents[0][scol], pevents[-1][scol],
        label1=beforel, label2=afterl, xlabel=slabel,
        title=title, subtitle=subtitle)
    png = FancyPlot(png, caption=plot.HEADER_CAPTION['HISTOGRAM'])
    plots.append(png)
    LOGGER.debug("Figure written to %s" % png)

    # efficiency/deadtime curve
    png = pngname % 'ROC'
    plot.hveto_roc(png, rounds, title=title, subtitle=subtitle)
    png = FancyPlot(png, caption=plot.HEADER_CAPTION['ROC'])
    plots.append(png)
    LOGGER.debug("Figure written to %s" % png)

    # frequency versus time
    png = pngname % '%s_TIME' % fcol.upper()
    labels = [str(r.n) for r in rounds]
    legtitle = 'Vetoed at\nround'
    plot.veto_scatter(
        png, pevents[0], pvetoed,
        label1='', label2=labels, title=title,
        subtitle=subtitle, ylabel=flabel, x='time', y=fcol,
        epoch=start, xlim=[start, end], legend_title=legtitle)
    png = FancyPlot(png, caption=plot.HEADER_CAPTION['TIME'])
    plots.append(png)
    LOGGER.debug("Figure written to %s" % png)

    # snr versus time
    png = pngname % 'SNR_TIME'
    plot.veto_scatter(
        png, pevents[0], pvetoed, label1='', label2=labels, title=title,
        subtitle=subtitle, ylabel=slabel, x='time', y=scol,
        epoch=start, xlim=[start, end], legend_title=legtitle)
    png = FancyPlot(png, caption=plot.HEADER_CAPTION['SNR_TIME'])
    plots.append(png)
    LOGGER.debug("Figure written to %s" % png)

    # -- write summary states to ASCII table and JSON
    json_ = {
        'user': getuser(),
        'host': getfqdn(),
        'date': str(datetime.datetime.now()),
        'configuration': inifile,
        'ifo': ifo,
        'gpsstart': start,
        'gpsend': end,
        'call': ' '.join(sys.argv),
        'rounds': [],
    }
    with open('summary-stats.txt', 'w') as f:
        # print header
        print('#N winner window SNR significance nveto use-percentage '
              'efficiency deadtime cumulative-efficiency cumulative-deadtime',
              file=f)
        for r in rounds:
            # extract relevant statistics
            results = [
                ('round', r.n),
                ('name', r.winner.name),
                ('window', r.winner.window),
                ('snr', r.winner.snr),
                ('significance', r.winner.significance),
                ('nveto', r.efficiency[0]),
                ('use-percentage',
                    r.use_percentage[0] / r.use_percentage[1] * 100.),
                ('efficiency', r.efficiency[0] / r.efficiency[1] * 100.),
                ('deadtime', r.deadtime[0] / r.deadtime[1] * 100.),
                ('cumulative-efficiency',
                    r.cum_efficiency[0] / r.cum_efficiency[1] * 100.),
                ('cumulative-deadtime',
                    r.cum_deadtime[0] / r.cum_deadtime[1] * 100.),
            ]
            # write to ASCII
            print(' '.join(map(str, list(zip(*results))[1])), file=f)
            # write to JSON
            results.append(('files', r.files))
            json_['rounds'].append(dict(results))
    LOGGER.debug("Summary table written to %s" % f.name)

    with open('summary-stats.json', 'w') as f:
        json.dump(json_, f, sort_keys=True)
    LOGGER.debug("Summary JSON written to %s" % f.name)

    # -- generate workflow for omega scans

    if args.omega_scans:
        omegatimes = list(map(str, sorted(numpy.unique(
            [t['time'] for r in rounds for t in r.scans]))))
        LOGGER.debug("Collected %d times to omega scan" % len(omegatimes))
        newtimes = [t for t in omegatimes if not
                    os.path.exists(os.path.join(omegadir, str(t)))]
        LOGGER.debug("%d scans already complete or in progress, %d remaining"
                     % (len(omegatimes) - len(newtimes), len(newtimes)))
        if len(newtimes) > 0:
            LOGGER.info('Creating workflow for omega scans')
            flags = batch.get_command_line_flags(
                ifo=ifo,
                ignore_state_flags=True)
            condorcmds = batch.get_condor_arguments(
                timeout=4,
                gps=start)
            batch.generate_dag(
                newtimes,
                flags=flags,
                submit=True,
                outdir=omegadir,
                condor_commands=condorcmds)
            LOGGER.info('Launched {} omega scans to condor'.format(
                len(newtimes)))
        else:
            LOGGER.debug('Skipping omega scans')

    # -- write HTML and finish

    index = html.write_hveto_page(
        ifo, start, end, rounds, plots,
        winners=[r.winner.name for r in rounds], **htmlv)
    LOGGER.debug("HTML written to %s" % index)
    LOGGER.debug("Analysis completed in %d seconds" % (time.time() - JOBSTART))
    LOGGER.info("-- Hveto complete --")


# -- run code -----------------------------------------------------------------

if __name__ == "__main__":
    main()
