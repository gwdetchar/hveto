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

from hveto import (__version__, config, core, plot, html, utils)

from .html import (wrap_html, bold_param)
from gwdetchar.io import html as gwhtml

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Josh Smith, Joe Areeda'

# -- HTML construction --------------------------------------------------------

#safety study html
# reminder: wrap_html automatically prepends the (ifo, start, end) args,
# and at least the outdir kwarg, so you should include those in the docstring,
# but not in the actual function declaration - the decorator will take care of
# that for you.

@wrap_html
def write_hveto_safety_page(rounds, thresh):
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
    page.caption("Summary of this HierarchichalVeto safety analysis.")
    l = gwhtml.html_link("./safety_summary.csv", 'Channel summary as CSV')
    page.add(bold_param('Download channel summary', l))
    l = gwhtml.html_link('./omega_times.txt', 'times for omega')
    page.add(bold_param('Download omega times (to run wdq_batch)', l))

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
                row_class = 'row-uu'
                safety_status = 'uns-uns'
            else:
                row_class = 'row-us'
                safety_status = 'uns-saf'
        elif round.winner.significance >= thresh:
            row_class = 'row-su'
            safety_status = 'saf-uns'
        else:
            row_class = 'row-ss'
            safety_status = 'saf-saf'

        page.tr(_class=row_class)
        # link round down page
        page.td(gwhtml.html_link('./hveto-round-%04d-summary.html' % round.n, round.n, target='_blank',
                          title="Jump to round %d details" % round.n), _class=row_class)
        # link name to CIS
        page.td(gwhtml.cis_link(round.winner.name))
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
def write_safety_round(round, thresh):
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


    # for desc, tag in zip(
    #         ['Veto segments', 'Veto triggers', 'Vetoed primary triggers',
    #          'Unvetoed primary triggers'],
    #         ['VETO_SEGS', 'WINNER', 'VETOED', 'RAW']):
    #     if isinstance(round.files[tag], str):
    #         files = [round.files[tag]]
    #     else:
    #         files = round.files[tag]
    #     link = ' '.join([gwhtml.html_link(
    #         f, '[%s]' % os.path.splitext(f)[1].strip('.')) for f in files])
    #     page.add(bold_param(desc, link))
    # link omega scans if generated
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
