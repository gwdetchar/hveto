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

import os.path
from functools import wraps

from MarkupPy import markup

from gwdetchar.io import html as gwhtml

from ._version import get_versions

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Josh Smith, Joe Areeda, Alex Urban'


# -- HTML construction --------------------------------------------------------

def navbar(ifo, gpstime, winners=[]):
    """Initialise a new `markup.page`

    Parameters
    ----------
    ifo : `str`
        the interferometer prefix

    gpstime : `float`
        the central GPS time of the analysis

    winners : `list`
        list of round winners for navbar table of contents

    Returns
    -------
    page : `markup.page`
        the structured markup to open an HTML document
    """
    (brand, class_) = gwhtml.get_brand(ifo, 'Hveto', gpstime, about='about')
    # channel navigation
    links = [['Summary', '#']]
    if not winners:
        links.append(['Rounds', '#rounds'])
    else:
        winners = [['%d: %s' % (i + 1, channel), '#hveto-round-%s' % (i + 1)]
                   for i, channel in enumerate(winners)]
        links.append(['Rounds', winners])
    return gwhtml.navbar(links, brand=brand, class_=class_)


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
    page.h1("%s HierarchicalVeto" % ifo, class_='pb-2 mt-3 mb-2 border-bottom')
    page.h3("%d-%d" % (start, end), class_='mt-3')
    page.div.close()
    return page()


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
        nav = navbar(ifo, start, winners)
        page = gwhtml.new_bootstrap_page(navbar=nav, **initargs)
        page.add(banner(ifo, start, end))
        # write content
        page.add(str(func(*args, **kwargs)))
        # close page with custom footer
        index = os.path.join(outdir, 'index.html')
        version = get_versions()['version']
        commit = get_versions()['full-revisionid']
        url = 'https://github.com/gwdetchar/hveto/tree/{}'.format(commit)
        gwhtml.close_page(page, index, about=about,
                          link=('hveto-%s' % version, url, 'GitHub'),
                          issues='https://github.com/gwdetchar/hveto/issues')
        return index
    return decorated_func


# -- Utilities ----------------------------------------------------------------

def bold_param(key, value, **attrs):
    """Write a (key, value) pair in HTML as ``<p><b>key</b>: value</p>``

    Parameters
    ----------
    key : `str`
        the element to be rendered in bold
    value : `str`
        the explanation/description of the key
    **attrs
        HTML attributes for the containing ``<p>`` tag

    Returns
    -------
    html : `str`
    """
    return markup.oneliner.p('<b>%s</b>: %s' % (key, value), **attrs)


# -- Hveto HTML ---------------------------------------------------------------

def write_summary(
        rounds, plots=[], header='Summary', plotsperrow=4,
        tableclass='table table-sm table-hover'):
    """Write the Hveto analysis summary HTML

    Parameters
    ----------
    rounds : `list` of `HvetoRound`
        the `list` of round objects produced by this analysis
    plots : `list` of `str`, optional
        the `list` of summary plots to display underneath the summary table
    header : `str`, optional
        the text for the section header (``<h2``>)
    plotsperrow : `int`, optional
        the number of plots to display in each row
    tableclass : `str`, optional
        the ``class`` for the summary ``<table>``

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the formatted markup object containing the analysis summary table,
        and images
    """
    page = markup.page()
    page.h2(header, class_='mt-4')
    page.table(class_=tableclass)
    page.caption("Summary of this HierarchichalVeto analysis.")
    # make header
    page.thead()
    page.tr()
    for header in ['Round', 'Winner', 'Twin [s]', 'SNR Thresh', 'Significance',
                   'Use [%]', 'Efficiency [%]', 'Deadtime [%]',
                   'Cum. efficiency [%]', 'Cum. deadtime [%]']:
        page.th(header, scope='row')
    page.tr.close()
    page.thead.close()
    # make body
    page.tbody()
    for r in rounds:
        page.tr()
        # link round down page
        page.td(gwhtml.html_link(
            '#hveto-round-%d' % r.n, r.n, target=None,
            title="Jump to round %d details" % r.n,
            style='color: inherit;',
        ))
        # link name to CIS
        page.td(gwhtml.cis_link(r.winner.name))
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
            if attr.endswith('deadtime'):
                page.td('%.2f<br><small>[%.2f/%.2f]</small>' % (pc, a, b))
            else:
                page.td('%.2f<br><small>[%d/%d]</small>' % (pc, a, b))
        page.tr.close()
    page.tbody.close()

    page.table.close()

    # scaffold plots
    if plots:
        page.div(class_='card border-light card-body scaffold shadow-sm')
        page.add(gwhtml.scaffold_plots(plots, nperrow=plotsperrow))
        page.div.close()  # card border-light card-body scaffold shadow-sm
    return page()


def write_round(round_, context):
    """Write the HTML summary for a specific round

    Parameters
    ----------
    round_ : `HvetoRound`
        the analysis round object

    context : `str`
        context for bootstrap objects, default: info

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the formatted HTML for this round
    """
    page = markup.page()
    page.div(class_='card card-%s mb-3 shadow-sm' % context)
    # -- make heading
    page.div(class_='card-header pb-0')
    # heading
    page.h5('Round %d, Winner = %s, window = %s, SNR thresh = %s'
            % (round_.n, round_.winner.name, round_.winner.window,
               round_.winner.snr),
            class_='card-title', id_='hveto-round-%d' % round_.n)
    page.div.close()  # card-header pb-0

    # -- make body
    page.div(class_='card-body')
    page.ul(class_='list-group')
    page.li(class_='list-group-item flex-column align-items-start')
    page.div(class_='row')
    # summary information
    page.div(class_='col-md-3', id_='hveto-round-%d-summary' % round_.n)
    page.add(bold_param('Winner', round_.winner.name))
    page.add(bold_param('SNR threshold', round_.winner.snr))
    page.add(bold_param('Window', round_.winner.window))
    page.add(bold_param('Significance', '%.2f' % round_.winner.significance))
    for desc, tag in zip(
            ['Veto segments', 'Veto triggers', 'Vetoed primary triggers',
             'Unvetoed primary triggers'],
            ['VETO_SEGS', 'WINNER', 'VETOED', 'RAW']):
        if isinstance(round_.files[tag], str):
            files = [round_.files[tag]]
        else:
            files = round_.files[tag]
        link = ' '.join([gwhtml.html_link(
            f, '[%s]' % os.path.splitext(f)[1].strip('.'),
            style='color: inherit;') for f in files])
        page.add(bold_param(desc, link))
    # link omega scans if generated
    if round_.scans is not None:
        page.p('<b>Omega scans:</b>')
        for t in round_.scans:
            page.p()
            page.a('%s [SNR %.1f]' % (t['time'], t[round_.rank]),
                   href='./scans/%s/' % t['time'], **{
                       'class_': 'fancybox',
                       'style': 'color: inherit;',
                       'target': '_blank'})
            for c, tag in zip([round_.primary, round_.winner.name],
                              ['Primary', 'Auxiliary']):
                caption = 'Omega scan of %s at %s' % (c, t['time'])
                png = ('./scans/%s/plots/%s-qscan_whitened-1.png'
                       % (t['time'], c.replace('-', '_').replace(':', '-')))
                page.a('[%s]' % tag[0].lower(), class_='fancybox',
                       href=png, title=caption,
                       style='color: inherit;',
                       **{'data-fancybox-group': 'omega-preview',
                          'data-fancybox': 'gallery'})
            page.p.close()
    page.div.close()  # col
    # plots
    page.div(class_='col-md-9', id_='hveto-round-%d-plots' % round_.n)
    page.add(gwhtml.scaffold_plots(round_.plots[:-1], nperrow=4))
    # add significance drop plot at end
    page.div(class_='row')
    page.div(class_='col-sm-12')
    page.add(gwhtml.fancybox_img(round_.plots[-1], lazy=True))
    page.div.close()  # col-sm-12
    page.div.close()  # row
    page.div.close()  # col-md-8

    page.div.close()  # row
    page.li.close()  # list-group-item flex-column align-items-start
    page.ul.close()  # list-group
    # close and return
    page.div.close()  # card-body
    page.div.close()  # card
    return page()


# reminder: wrap_html automatically prepends the (ifo, start, end) args,
# and at least the outdir kwarg, so you should include those in the docstring,
# but not in the actual function declaration - the decorator will take care of
# that for you.

@wrap_html
def write_hveto_page(rounds, plots, context='default'):
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
    plots : `list` of `str`
        the `list` of summary plots
    outdir : `str`, optional
        the output directory for the HTML
    winners : `list` of `str`, optional
        list of channels that won each round
    context : `str`, optional
        the bootstrap context class for this result, see the bootstrap
        docs for more details

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    page = markup.page()
    page.add(write_summary(rounds, plots))
    page.h2('Round details', class_='mt-4', id_='rounds')
    for r in rounds:
        page.add(write_round(r, context=context))
    return page


@wrap_html
def write_null_page(reason, context='info'):
    """Write the Hveto results to HTML

    Parameters
    ----------
    ifo : `str`
        the prefix of the interferometer used in this analysis
    start  : `int`
        the GPS start time of the analysis
    end : `int`
        the GPS end time of the analysis
    reason : `str`
        the explanation for this null result
    context : `str`, optional
        the bootstrap context class for this result, see the bootstrap
        docs for more details
    outdir : `str`, optional
        the output directory for the HTML

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    return gwhtml.alert(reason, context=context, dismiss=False)


@wrap_html
def write_about_page(configfile):
    """Write a page explaining how an hveto analysis was completed

    Parameters
    ----------
    ifo : `str`
        the prefix of the interferometer used in this analysis
    start  : `int`
        the GPS start time of the analysis
    end : `int`
        the GPS end time of the analysis
    configfile : `str`
        the path of the configuration file to embed
    outdir : `str`, optional
        the output directory for the HTML

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    return gwhtml.about_this_page(configfile)
