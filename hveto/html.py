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

"""HTML utilities for hveto
"""

from __future__ import division

import os.path

from glue import markup

from . import version

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Josh Smith, Joe Areeda'
__version__ = version.version

JQUERY_JS = "//code.jquery.com/jquery-1.11.2.min.js"

BOOTSTRAP_CSS = (
    "//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css")
BOOTSTRAP_JS = (
    "//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js")


def write_summary(rounds, plots=[]):
    page = markup.page()
    page.h2('Summary')
    page.table(class_='table table-condensed table-hover table-responsive')
    # make header
    page.thead()
    page.tr()
    for header in ['Round', 'Winner', 'Twin [s]', 'SNR Thresh', 'Significance',
                   'Use [%]', 'Efficiency [%]', 'Deadtime [%]',
                   'Cum. efficiency [%]', 'Cum. deadtime [%]']:
        page.th(header)
    page.tr.close()
    page.thead.close()
    # make body
    page.tbody()
    for r in rounds:
        page.tr()
        page.td(r.n)
        for attr in ['name', 'window', 'snr', 'significance']:
            v = getattr(r.winner, attr)
            if isinstance(v, float):
                page.td('%.2f' % v)
            else:
                page.td(str(v))
        for attr in ['use_percentage', 'efficiency', 'deadtime',
                     'cum_efficiency', 'cum_deadtime']:
            a, b = getattr(r, attr)
            try:
                pc = a/b * 100.
            except ZeroDivisionError:
                pc = 0.
            page.td('%.2f<br><small>[%d/%d]</small>' % (pc, a, b))
        page.tr.close()
    page.tbody.close()

    page.table.close()

    # scaffold plots
    if plots:
        page.add(scaffold_plots(plots, nperrow=4))
    return page()


def write_round(round):
    """Write the HTML summary for a specific round
    """
    page = markup.page()
    page.div(class_='panel panel-info', id_='round-%d' % round.n)
    # -- make heading
    page.div(class_='panel-heading')
    page.h3('Round %d, Winner = %s, window = %s, SNR thresh = %s'
            % (round.n, round.winner.name, round.winner.window,
               round.winner.snr), class_='panel-title')
    page.div.close()  # panel-heading

    # -- make body
    page.div(class_='panel-body')
    page.div(class_='row')
    # summary information
    page.div(class_='col-md-3', id_='round-%d-summary' % round.n)
    page.add(bold_param('Winner', round.winner.name))
    page.add(bold_param('SNR threshold', round.winner.snr))
    page.add(bold_param('Window', round.winner.window))
    page.add(bold_param('Significance', '%.2f' % round.winner.significance))
    page.div.close()  # col
    # plots
    page.div(class_='col-md-9', id_='round-%d-plots' % round.n)
    page.add(scaffold_plots(round.plots[:-1], nperrow=4))
    # add significance drop plot at end
    page.div(class_='row')
    page.div(class_='col-sm-12')
    page.add(image_markup(round.plots[-1]))
    page.div.close()  # col-sm-12
    page.div.close()  # row
    page.div.close()  # col-md-8

    page.div.close()  # row
    # close and return
    page.div.close()  # panel-body
    page.div.close()  # panel
    return page()


def bold_param(key, value):
    return markup.oneliner.p('<b>%s</b>: %s' % (key, value))


def image_markup(img):
    """Return the markup to embed an <img> in HTML
    """
    page = markup.page()
    imgname = os.path.basename(img)
    page.a(href=img, target='_blank', title=imgname)
    page.img(src=img, alt=imgname, class_='img-responsive')
    page.a.close()
    return str(page)


def scaffold_plots(plots, nperrow=2):
    page = markup.page()
    x = int(12//nperrow)
    # scaffold plots
    for i, p in enumerate(plots):
        if i % nperrow == 0:
            page.div(class_='row')
        page.div(class_='col-sm-%d' % x)
        page.add(image_markup(p))
        page.div.close()  # col
        if i % nperrow == nperrow - 1:
            page.div.close()  # row
    if i % nperrow < nperrow-1:
        page.div.close()  # row
    return page()


def write_hveto_page(rounds, plots, ifo, start, end,
                     outdir=os.path.curdir, **kwargs):
    """Write the Hveto results to HTML
    """
    page = markup.page()

    # add bootstrap CSS and JS if needed
    css = kwargs.pop('css', [])
    if BOOTSTRAP_CSS not in css:
        css.insert(0, BOOTSTRAP_CSS)
    script = kwargs.pop('script', [])
    for js in [BOOTSTRAP_JS, JQUERY_JS]:
        if js not in script:
            script.insert(0, js)

    # create page and init
    kwargs['css'] = css
    kwargs['script'] = script
    page.init(**kwargs)

    # write banner
    page.div(class_='container')
    page.div(class_='page-header', role='banner')
    page.h1("%s HierarchicalVeto" % ifo)
    page.h3("%d-%d" % (start, end))
    page.div.close()
    page.div.close()  # container

    # write content
    page.div(class_='container')
    page.div('', id_='content')
    content = markup.page()
    content.add(write_summary(rounds, plots))
    content.h2('Round details')
    for r in rounds:
        content.add(write_round(r))
    contentf = os.path.join(outdir, 'content.html')
    with open(contentf, 'w') as f:
        f.write(content())
    # load content
    page.script("$('#content').load('%s');" % contentf)
    page.div.close()  # container

    # close
    page.body.close()
    page.html.close()

    # write index
    index = os.path.join(outdir, 'index.html')
    with open(index, 'w') as f:
        f.write(page())
    return index
