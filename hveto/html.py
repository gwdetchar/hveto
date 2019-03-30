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
from functools import wraps

from MarkupPy import markup

from gwdetchar.io import html as gwhtml

from ._version import get_versions

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Josh Smith, Joe Areeda, Alex Urban'


# -- HTML construction --------------------------------------------------------

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
    page.div(class_='container')
    page.div(class_='page-header', role='banner')
    page.h1("%s HierarchicalVeto" % ifo)
    page.h3("%d-%d" % (start, end))
    page.div.close()
    page.div.close()  # container
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
        header = banner(ifo, start, end)
        page = gwhtml.new_bootstrap_page(navbar=header, **initargs)
        # write content
        contentf = os.path.join(outdir, '_inner.html')
        with open(contentf, 'w') as f:
            f.write(str(func(*args, **kwargs)))
        # embed content
        page.div('', id_='content')
        page.script("$('#content').load('%s');" % contentf)
        # close page with custom footer
        index = os.path.join(outdir, 'index.html')
        version = get_versions()['version']
        commit = get_versions()['full-revisionid']
        url = 'https://github.com/gwdetchar/hveto/tree/{}'.format(commit)
        link = markup.oneliner.a(
            'View hveto-{} on GitHub'.format(version), href=url,
            target='_blank', style='color:#eee;')
        report = 'https://github.com/gwdetchar/hveto/issues'
        issues = markup.oneliner.a(
            'Report an issue', href=report, target='_blank',
            style='color:#eee;')
        gwhtml.close_page(page, index, about=about, link=link, issues=issues)
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
        tableclass='table table-condensed table-hover table-responsive'):
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
    page.h2(header)
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
        page.td(gwhtml.html_link('#hveto-round-%d' % r.n, r.n, target=None,
                                 title="Jump to round %d details" % r.n))
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
        page.add(gwhtml.scaffold_plots(plots, nperrow=plotsperrow))
    return page()


def write_round(round):
    """Write the HTML summary for a specific round

    Parameters
    ----------
    round : `HvetoRound`
        the analysis round object

    Returns
    -------
    page : `~MarkupPy.markup.page`
        the formatted HTML for this round
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
        link = ' '.join([gwhtml.html_link(
            f, '[%s]' % os.path.splitext(f)[1].strip('.')) for f in files])
        page.add(bold_param(desc, link))
    # link omega scans if generated
    if round.scans is not None:
        page.p('<b>Omega scans:</b>')
        for t in round.scans:
            page.p()
            page.a('%s [SNR %.1f]' % (t['time'], t['snr']),
                href='./scans/%s/' % t['time'], **{
                'class_': 'fancybox',
                'data-fancybox-group': 'hveto-image',
                'target': '_blank',
            })
            for c, tag in zip([round.primary, round.winner.name],
                              ['Primary', 'Auxiliary']):
                caption = 'Omega scan of %s at %s' % (c, t['time'])
                png = ('./scans/%s/plots/%s-qscan_whitened-1.png'
                       % (t['time'], c.replace('-', '_').replace(':', '-')))
                page.a('[%s]' % tag[0].lower(), class_='fancybox',
                       href=png, title=caption,
                       **{'data-fancybox-group': 'omega-preview'})
            page.p.close()
    page.div.close()  # col
    # plots
    page.div(class_='col-md-9', id_='hveto-round-%d-plots' % round.n)
    page.add(gwhtml.scaffold_plots(round.plots[:-1], nperrow=4))
    # add significance drop plot at end
    page.div(class_='row')
    page.div(class_='col-sm-12')
    page.add(gwhtml.fancybox_img(round.plots[-1]))
    page.div.close()  # col-sm-12
    page.div.close()  # row
    page.div.close()  # col-md-8

    page.div.close()  # row
    # close and return
    page.div.close()  # panel-body
    page.div.close()  # panel
    return page()


# reminder: wrap_html automatically prepends the (ifo, start, end) args,
# and at least the outdir kwarg, so you should include those in the docstring,
# but not in the actual function declaration - the decorator will take care of
# that for you.

@wrap_html
def write_hveto_page(rounds, plots):
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

    Returns
    -------
    index : `str`
        the path of the HTML written for this analysis
    """
    page = markup.page()
    page.add(write_summary(rounds, plots))
    page.h2('Round details')
    for r in rounds:
        page.add(write_round(r))
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
    page = markup.page()
    # write alert
    page.div(class_='alert alert-%s' % context)
    page.p(reason)
    page.div.close()  # alert
    return page


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
    # set up page
    page = markup.page()

    # command line
    page.h2('On the command line')
    page.p('This page was generated with the command line call shown below.')
    commandline = gwhtml.get_command_line()
    page.add(commandline)

    # configuration file
    page.h2('Configuration')
    with open(configfile, 'r') as fobj:
        inifile = fobj.read()
    contents = gwhtml.render_code(inifile, 'ini')
    page.add(contents)

    # runtime environment
    page.add(gwhtml.package_table())

    return page
