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

# -- set up default JS and CSS files

JQUERY_JS = "//code.jquery.com/jquery-1.11.2.min.js"

BOOTSTRAP_CSS = (
    "//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css")
BOOTSTRAP_JS = (
    "//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js")

FANCYBOX_CSS = (
    "//cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.css")
FANCYBOX_JS = (
    "//cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.js")

FONT_LATO_CSS = (
    "//fonts.googleapis.com/css?family=Lato:300,700"
)

CSS_FILES = [BOOTSTRAP_CSS, FANCYBOX_CSS, FONT_LATO_CSS]
JS_FILES = [JQUERY_JS, BOOTSTRAP_JS, FANCYBOX_JS]

# --


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
        # link round down page
        page.td(html_link('#hveto-round-%d' % r.n, r.n, target=None,
                          title="Jump to round %d details" % r.n))
        # link name to CIS
        page.td(html_link(
            "https://cis.ligo.org/channel/byname/%s" % r.winner.name,
            r.winner.name,
            style="font-family: Monaco, \"Courier New\", monospace;",
            title="CIS entry for %s" % r.winner.name,
        ))
        for attr in ['window', 'snr', 'significance']:
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
    page.div(class_='panel panel-info', id_='hveto-round-%d' % round.n)
    # -- make heading
    page.div(class_='panel-heading clearfix')
    # link to top of page
    page.div(class_='pull-right')
    page.a("<small>[top]</small>", href='#')
    page.div.close()  # pull-right
    # heading
    page.h3('Round %d, Winner = %s, window = %s, SNR thresh = %s'
            % (round.n, round.winner.name, round.winner.window,
               round.winner.snr), class_='panel-title')
    page.div.close()  # panel-heading

    # -- make body
    page.div(class_='panel-body')
    page.div(class_='row')
    # summary information
    page.div(class_='col-md-3', id_='hveto-round-%d-summary' % round.n)
    page.add(bold_param('Winner', round.winner.name))
    page.add(bold_param('SNR threshold', round.winner.snr))
    page.add(bold_param('Window', round.winner.window))
    page.add(bold_param('Significance', '%.2f' % round.winner.significance))
    for desc, tag in zip(
            ['Veto segments', 'Veto triggers', 'Vetoed primary triggers',
             'Unvetoed primary triggers'],
            ['VETO_SEGS', 'WINNER', 'VETOED', 'RAW']):
        if isinstance(round.files[tag], str):
            files = [round.files[tag]]
        else:
            files = round.files[tag]
        link = ' '.join([html_link(
            f, '[%s]' % os.path.splitext(f)[1].strip('.')) for f in files])
        page.add(bold_param(desc, link))
    page.div.close()  # col
    # plots
    page.div(class_='col-md-9', id_='hveto-round-%d-plots' % round.n)
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
    page.a(
        href=img, title=imgname,
        class_="fancybox", rel="hveto-image",  # hooks for fancybox
        target='_blank',  # open in new window/tab
    )
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
    for cssf in CSS_FILES[::-1]:
        b = os.path.basename(cssf)
        if not any(f.endswith(b) for f in css):
            css.insert(0, cssf)
    script = kwargs.pop('script', [])
    for jsf in JS_FILES[::-1]:
        b = os.path.basename(jsf)
        if not any(f.endswith(b) for f in script):
            script.insert(0, jsf)

    # create page and init
    kwargs['css'] = css
    kwargs['script'] = script
    kwargs.setdefault('bodyattrs', {
        'style': 'font-family: \"Lato\", \"Helvetica Neue\", '
                     'Helvetica, Arial, sans-serif; '
                 '-webkit-font-smoothing: antialiased;',
    })
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

    # run fancybox
    page.script("""
  $(document).ready(function() {
    $(\".fancybox\").fancybox({
      nextEffect: 'none',
      prevEffect: 'none',
    });
  });""")

    # close
    page.body.close()
    page.html.close()

    # write index
    index = os.path.join(outdir, 'index.html')
    with open(index, 'w') as f:
        f.write(page())
    return index


def html_link(href, txt, target="_blank", **params):
    if target is not None:
        params.setdefault('target', target)
    return markup.oneliner.a(txt, href=href, **params)
