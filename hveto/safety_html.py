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

"""HTML utilities for hveto safety studies, derived from hveto's html
"""

from __future__ import division

import sys
import os.path
import datetime
import subprocess
from functools import wraps
from getpass import getuser

from glue import markup
from astropy.time import Time

from hveto import (__version__, config, core, plot, html, utils)
from gwpy.time import tconvert

from .html import  (bold_param, write_about_page)
from gwdetchar.io import html as gwhtml
from gwdetchar.io.html import (OBSERVATORY_MAP, FancyPlot, cis_link)
from ._version import get_versions


__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Josh Smith, Joe Areeda'

# -- HTML construction --------------------------------------------------------

#safety study html
# reminder: wrap_html automatically prepends the (ifo, start, end) args,
# and at least the outdir kwarg, so you should include those in the docstring,
# but not in the actual function declaration - the decorator will take care of
# that for you.

def wrap_html(func):
    """Decorator to wrap a function with `init_page` and `close_page` calls

    This allows inner HTML methods to be written with minimal arguments
    and content, hopefully making things simpler
    """
    @wraps(func)
    def decorated_func(ifo, start, end, *args, **kwargs):
        # set page init args
        initargs = {
            'title': '%s Hveto | %d-%d' % (ifo, start, end),
            'base': os.path.curdir,
        }
        for key in ['title', 'base']:
            if key in kwargs:
                initargs[key] = kwargs.pop(key)
        # find outdir
        outdir = kwargs.pop('outdir', initargs['base'])
        winners = kwargs.pop('winners', [])
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        # write about page
        try:
            config = kwargs.pop('config')
        except KeyError:
            about = None
        else:
            iargs = initargs.copy()
            aboutdir = os.path.join(outdir, 'about')
            if iargs['base'] == os.path.curdir:
                iargs['base'] = os.path.pardir
            about = write_about_page(ifo, start, end, config, outdir=aboutdir,
                                     **iargs)
            if os.path.basename(about) == 'index.html':
                about = about[:-10]
        # open page
        page = gwhtml.new_bootstrap_page(navbar=None, **initargs)
        page.add(banner(ifo, start, end))
        # write content
        page.add(str(func(*args, **kwargs)))
        # close page with custom footer
        fname = 'index.html'
        if 'html_file' in kwargs:
            fname = kwargs['html_file']
        index = os.path.join('.', fname)
        version = get_versions()['version']
        commit = get_versions()['full-revisionid']
        url = 'https://github.com/gwdetchar/hveto/tree/{}'.format(commit)
        link = markup.oneliner.a(
            'View hveto-{} on GitHub'.format(version), href=url,
            target='_blank')
        report = 'https://github.com/gwdetchar/hveto/issues'
        issues = markup.oneliner.a(
            'Report an issue', href=report, target='_blank')
        gwhtml.close_page(page, index, about=about, link=link, issues=issues)
        return index
    return decorated_func


@wrap_html
def write_hveto_safety_page(rounds, thresh, inj_img=None):
    """Write the Hveto results to HTML

    Parameters
    ----------
    ifo : `str`
        the prefix of the interferometer used in this analysis
    start  : `int`
        the GPS start time of the analysis
    end : `int`
        the GPS end time of the analysis
    rounds : `list` of `HvetoRound`
        the rounds produced by this analysis
    thresh: significance threshold to be considered unsafe
    inj_img: png of time-freq x SNR injections
    plots : `list` of `str`
        the `list` of summary plots
    outdir : `str`, optional
        the output directory for the HTML

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """

    page = markup.page()
    page.h2("Hveto safety study")
    tableclass = 'table table-condensed table-hover table-responsive'
    page.table(class_=tableclass)
    page.caption("Summary of Hierarchical Veto safety analysis.")
    l = gwhtml.html_link('./safety_summary.csv', 'Channel summary as CSV')
    page.add(bold_param('Download channel summary', l))

    if os.path.exists('./omega_times.txt'):
        l = gwhtml.html_link('./omega_times.txt', 'times for omega')
        page.add(bold_param('Download omega times (to run wdq_batch)', l))

    if inj_img:
        caption = 'All injections'
        prim_plot = FancyPlot(inj_img, caption=caption)
        page.img(src=inj_img, class_='fancybox', alt=caption)
        page.br()

    # make channel table header
    page.thead()
    page.tr()
    for header in ['Round', 'Winner', 'Safety','Twin [s]', 'SNR Thresh', 'Significance',
                   'Use [%]', 'Efficiency [%]', 'Deadtime [%]']:
        page.th(header, scope='row')
    page.tr.close()
    page.thead.close()
    # make body
    page.tbody()
    for round in rounds:
        row_class = ''
        safety_status = ''

        if round.unsafe:
            if round.winner.significance >= thresh:
                row_class = 'row-uu panel-warning panel-heading'
                safety_status = 'uns-uns'
            else:
                row_class = 'row-us panel-success panel-heading'
                safety_status = 'uns-saf'
        elif round.winner.significance >= thresh:
            row_class = 'row-su panel-danger panel-heading'
            safety_status = 'saf-uns'
        else:
            row_class = 'row-ss panel-heading panel-info'
            safety_status = 'saf-saf'

        page.tr(_class=row_class)
        # link round down page
        page.td(gwhtml.html_link('./hveto-round-%04d-summary.html' % round.n, round.n, target='_blank',
                          title="Jump to round %d details" % round.n), _class=row_class)
        # link name to CIS
        page.td(gwhtml.cis_link(round.winner.name), _class=row_class)
        page.td(safety_status, _class=row_class)

        for attr in ['window', 'snr', 'significance']:
            v = getattr(round.winner, attr)
            if isinstance(v, float):
                page.td('%.2f' % v, _class=row_class)
            else:
                page.td(str(v), _class=row_class)
        for attr in ['use_percentage', 'efficiency', 'deadtime']:
            a, b = getattr(round, attr)
            try:
                pc = a / b * 100.
            except ZeroDivisionError:
                pc = 0.
            if attr.endswith('deadtime'):
                page.td('%.2f<br><small>[%.2f/%.2f]</small>' % (pc, a, b), _class=row_class)
            else:
                page.td('%.2f<br><small>[%d/%d]</small>' % (pc, a, b), _class=row_class)
        page.tr.close()
    page.tbody.close()

    page.table.close()

    return page


@wrap_html
def write_safety_round(round, thresh, write_about_file=False, html_file=None):
    """Write the HTML summary for a specific round

    Parameters
    ----------
    round : `HvetoRound`
        the analysis round object
    thresh: significance threshold to be considered unsafe

    Returns
    -------
    page : `~glue.markup.page`
        the formatted HTML for this round
    """
    page = markup.page()

    panel_bkg = ''
    safety_status = ''

    if round.unsafe:
        if round.winner.significance >= thresh:
            panel_bkg = ' panel-warning'
            safety_status = 'Unsafe - unsafe'
        else:
            panel_bkg = ' panel-success'
            safety_status = 'Unsafe - safe'
    elif round.winner.significance >= thresh:
        panel_bkg = ' panel-danger'
        safety_status = 'Safe - unsafe'
    else:
        panel_bkg = 'panel-info'
        safety_status = 'Safe - safe'

    page.div(class_='panel ' + panel_bkg, id_='hveto-round-%d' % round.n)
    # -- make heading
    page.div(class_='panel-heading clearfix ' + panel_bkg)
    # link to top of page
    page.div(class_='pull-right')
    page.a("<small>[top]</small>", href='#')
    page.div.close()  # pull-right
    # heading
    page.h3('Round %d, channel = %s, window = %s, SNR thresh = %s, significane = %.1f'
            % (round.n, round.winner.name, round.winner.window,
               round.winner.snr, round.winner.significance), class_='panel-title ' + panel_bkg)
    page.div.close()  # panel-heading

    # -- make body
    page.div(class_='panel-body')
    page.div(class_='row')
    # summary information
    page.div(class_='col-md-3', id_='hveto-round-%04d-summary' % round.n)
    page.add(bold_param('Winner', round.winner.name))
    page.add(bold_param('SNR threshold', round.winner.snr))
    page.add(bold_param('Window', round.winner.window))
    page.add(bold_param('Significance', '%.2f' % round.winner.significance))
    page.add(bold_param('Safety', safety_status))
    try:
        pc = round.use_percentage[0] / round.use_percentage[1] * 100.
    except ZeroDivisionError:
        pc = 0.
    page.add(bold_param('Use percentage',
                        ('%.2f [%d/%d]' % (pc, round.use_percentage[0], round.use_percentage[1]))))

    try:
        pc = round.efficiency[0] / round.efficiency[1] * 100.
    except ZeroDivisionError:
        pc = 0.
    page.add(bold_param('Efficiency',
                        ('%.2f [%d/%d]' % (pc, round.efficiency[0], round.efficiency[1]))))

    try:
        pc = round.deadtime[0] / round.deadtime[1] * 100.
    except ZeroDivisionError:
        pc = 0.
    page.add(bold_param('Deadtime',
                        ('%.2f [%.2f/%.2f]' % (pc, round.deadtime[0], round.deadtime[1]))))



    if round.scans is not None:
        page.p('<b>Omega scans:</b>')
        for t in round.scans:
            primary_channel = round.primary[0][3]
            page.p()
            page.a('%s [SNR %.1f]' % (t['time'], t['snr']),
                href='./scans/%s/' % t['time'], **{
                'class_': 'fancybox',
                'data-fancybox-group': 'hveto-image',
                'target': '_blank',
            })
            for c, tag in zip([primary_channel, round.winner.name],
                              ['Primary', 'Auxiliary']):
                caption = 'Omega scan of %s at %s' % (c, t['time'])
                png = ('./scans/%s/%s_%s_1.00_spectrogram_whitened.png'
                       % (t['time'], t['time'], c))
                img = FancyPlot(png, caption)
                page.a('[%s]' % tag[0].lower(), class_='fancybox',
                       href=png, title=caption,
                       **{'data-fancybox-group': 'omega-preview'})
            page.p.close()
    page.div.close()  # col
    # plots
    page.div(class_='col-md-9', id_='hveto-round-%d-plots' % round.n)
    page.add(gwhtml.scaffold_plots(round.plots, nperrow=4))
    # add significance drop plot at end

    page.div.close()  # col-md-8

    page.div.close()  # row
    # close and return
    page.div.close()  # panel-body
    page.div.close()  # panel
    return page()

def banner(ifo, start, end):
    """Initialise a new markup banner

    Parameters
    ----------
    ifo : `str`
        the interferometer prefix
    start : `int`
        the GPS start time of the analysis
    end : `int`
        the GPS end time of the analysis

    Returns
    -------
    page : `markup.page`
        the structured markup to open an HTML document
    """
    # create page
    page = markup.page()
    # write banner
    page.div(class_='page-header', role='banner')
    page.h1("%s Hierarchical Veto" % ifo)
    start_utc = tconvert(start)
    end_utc = tconvert(end)
    page.h3('{:d}-{:d}'.format(int(start), int(end)))
    page.h3('{:s} to {:s}'.format(str(start_utc), str(end_utc)))
    page.div.close()
    return page()

def gps2utc(gps):
    """Convert GPS time to string"""
    gps_time = Time(int(gps), format='gps', scale='utc')
    utc = gps_time.datetime.strftime('%Y-%m-%d %H:%M:%S')
    return utc
