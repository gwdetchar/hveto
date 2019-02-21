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

import sys
import os.path
import datetime
import subprocess
from functools import wraps
from getpass import getuser

from glue import markup

from ._version import get_versions

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Josh Smith, Joe Areeda, Alex Urban'

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

CSS_FILES = [BOOTSTRAP_CSS, FANCYBOX_CSS]
JS_FILES = [JQUERY_JS, BOOTSTRAP_JS, FANCYBOX_JS]

HVETO_CSS = """
html {
		position: relative;
		min-height: 100%;
}
body {
		margin-bottom: 120px;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		-webkit-font-smoothing: antialiased;
}
.footer {
		position: absolute;
		bottom: 0;
		width: 100%;
		height: 100px;
		background-color: #f5f5f5;
		padding-top: 20px;
		padding-bottom: 20px;
}
.fancybox-skin {
		background: white;
}
"""

HVETO_JS = """
$(document).ready(function() {
	$(\".fancybox\").fancybox({
		nextEffect: 'none',
		prevEffect: 'none',
		helpers: {title: {type: 'inside'}}
	});
});
"""


# -- HTML construction --------------------------------------------------------

def write_static_files(static):
    """Write static CSS and javascript files into the given directory

    Parameters
    ----------
    static : `str`
        the target directory for the static files, will be created if
        necessary

    Returns
    -------
    `<statc>/hveto.css`
    `<static>/hveto.js`
        the paths of the two files written by this method, which will be
        `hveto.css` and `hveto.js` inside `static`

    Notes
    -----
    This method modifies the module-level variables ``CSS_FILES` and
    ``JS_FILES`` to guarantee that the static files are actually only
    written once per process.
    """
    if not os.path.isdir(static):
        os.makedirs(static)
    hvetocss = os.path.join(static, 'hveto.css')
    if hvetocss not in CSS_FILES:
        with open(hvetocss, 'w') as f:
            f.write(HVETO_CSS)
        CSS_FILES.append(hvetocss)
    hvetojs = os.path.join(static, 'hveto.js')
    if hvetojs not in JS_FILES:
        with open(hvetojs, 'w') as f:
            f.write(HVETO_JS)
        JS_FILES.append(hvetojs)
    return hvetocss, hvetojs


def init_page(ifo, start, end, css=[], script=[], base=os.path.curdir,
              **kwargs):
    """Initialise a new `markup.page`

    This method constructs an HTML page with the following structure

    .. code-block:: html

        <html>
        <head>
            <!-- some stuff -->
        </head>
        <body>
        <div class="container">
        <div class="page-header">
        <h1>IFO</h1>
        <h3>START-END</h3>
        </div>
        </div>
        <div class="container">

    Parameters
    ----------
    ifo : `str`
        the interferometer prefix
    start : `int`
        the GPS start time of the analysis
    end : `int`
        the GPS end time of the analysis
    css : `list`, optional
        the list of stylesheets to link in the `<head>`
    script : `list`, optional
        the list of javascript files to link in the `<head>`
    base : `str`, optional, default '.'
        the path for the `<base>` tag to link in the `<head>`

    Returns
    -------
    page : `markup.page`
        the structured markup to open an HTML document
    """
    # write CSS to static dir
    staticdir = os.path.join(os.path.curdir, 'static')
    write_static_files(staticdir)
    # create page
    page = markup.page()
    page.header.append('<!DOCTYPE HTML>')
    page.html(lang='en')
    page.head()
    page.base(href=base)
    page._full = True
    # link stylesheets (appending bootstrap if needed)
    css = css[:]
    for cssf in CSS_FILES[::-1]:
        b = os.path.basename(cssf)
        if not any(f.endswith(b) for f in css):
            css.insert(0, cssf)
    for f in css:
        page.link(href=f, rel='stylesheet', type='text/css', media='all')
    # link javascript
    script = script[:]
    for jsf in JS_FILES[::-1]:
        b = os.path.basename(jsf)
        if not any(f.endswith(b) for f in script):
            script.insert(0, jsf)
    for f in script:
        page.script('', src=f, type='text/javascript')
    # add other attributes
    for key in kwargs:
        getattr(page, key)(kwargs[key])
    # finalize header
    page.head.close()
    page.body()
    # write banner
    page.div(class_='container')
    page.div(class_='page-header', role='banner')
    page.h1("%s HierarchicalVeto" % ifo)
    page.h3("%d-%d" % (start, end))
    page.div.close()
    page.div.close()  # container

    # open container
    page.div(class_='container')
    return page


def close_page(page, target, about=None, date=None):
    """Close an HTML document with markup then write to disk

    This method writes the closing markup to complement the opening
    written by `init_page`, something like:

    .. code-block:: html

       </div>
       <footer>
           <!-- some stuff -->
       </footer>
       </body>
       </html>

    Parameters
    ----------
    page : `markup.page`
        the markup object to close
    target : `str`
        the output filename for HTML
    about : `str`, optional
        the path of the 'about' page to link in the footer
    date : `datetime.datetime`, optional
        the timestamp to place in the footer, defaults to
        `~datetime.datetime.now`
    """
    page.div.close()  # container
    page.add(str(write_footer(about=about, date=date)))
    if not page._full:
        page.body.close()
        page.html.close()
    with open(target, 'w') as f:
        f.write(page())
    return page


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
        page = init_page(ifo, start, end, **initargs)
        # write content
        contentf = os.path.join(outdir, '_inner.html')
        with open(contentf, 'w') as f:
            f.write(str(func(*args, **kwargs)))
        # embed content
        page.div('', id_='content')
        page.script("$('#content').load('%s');" % contentf)
        # close page
        index = os.path.join(outdir, 'index.html')
        close_page(page, index, about=about)
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


def html_link(href, txt, target="_blank", **params):
    """Write an HTML <a> tag

    Parameters
    ----------
    href : `str`
        the URL to point to
    txt : `str`
        the text for the link
    target : `str`, optional
        the ``target`` of this link
    **params
        other HTML parameters for the ``<a>`` tag

    Returns
    -------
    html : `str`
    """
    if target is not None:
        params.setdefault('target', target)
    return markup.oneliner.a(txt, href=href, **params)


def cis_link(channel, **params):
    """Write a channel name as a link to the Channel Information System

    Parameters
    ----------
    channel : `str`
        the name of the channel to link
    **params
        other HTML parmeters for the ``<a>`` tag

    Returns
    -------
    html : `str`
    """
    kwargs = {
        'title': "CIS entry for %s" % channel,
        'style': "font-family: Monaco, \"Courier New\", monospace;",
    }
    kwargs.update(params)
    return html_link("https://cis.ligo.org/channel/byname/%s" % channel,
                     channel, **kwargs)


def fancybox_img(img, linkparams=dict(), **params):
    """Return the markup to embed an <img> in HTML

    Parameters
    ----------
    img : `FancyPlot`
        a `FancyPlot` object containing the path of the image to embed
        and its caption to be displayed
    linkparams : `dict`
        the HTML attributes for the ``<a>`` tag
    **params
        the HTML attributes for the ``<img>`` tag

    Returns
    -------
    html : `str`

    Notes
    -----
    See `~hveto.plot.FancyPlot` for more about the `FancyPlot` class.
    """
    page = markup.page()
    aparams = {
        'title': img.caption,
        'class_': 'fancybox',
        'target': '_blank',
        'data-fancybox-group': 'hveto-image',
    }
    aparams.update(linkparams)
    img = str(img)
    page.a(href=img, **aparams)
    imgparams = {
        'alt': os.path.basename(img),
        'class_': 'img-responsive',
    }
    if img.endswith('.svg') and os.path.isfile(img.replace('.svg', '.png')):
        imgparams['src'] = img.replace('.svg', '.png')
    else:
        imgparams['src'] = img
    imgparams.update(params)
    page.img(**imgparams)
    page.a.close()
    return str(page)


def scaffold_plots(plots, nperrow=2):
    """Embed a `list` of images in a bootstrap scaffold

    Parameters
    ----------
    plot : `list` of `str`
        the list of image paths to embed
    nperrow : `int`
        the number of images to place in a row (on a desktop screen)

    Returns
    -------
    page : `~glue.markup.page`
        the markup object containing the scaffolded HTML
    """
    page = markup.page()
    x = int(12//nperrow)
    # scaffold plots
    for i, p in enumerate(plots):
        if i % nperrow == 0:
            page.div(class_='row')
        page.div(class_='col-sm-%d' % x)
        page.add(fancybox_img(p))
        page.div.close()  # col
        if i % nperrow == nperrow - 1:
            page.div.close()  # row
    if i % nperrow < nperrow-1:
        page.div.close()  # row
    return page()


def write_footer(about=None, date=None):
    """Write a <footer> for an Hveto page

    Parameters
    ----------
    about : `str`, optional
        path of about page to link
    date : `datetime.datetime`, optional
        the datetime representing when this analysis was generated, defaults
        to `~datetime.datetime.now`

    Returns
    -------
    page : `~glue.markup.page`
        the markup object containing the footer HTML
    """
    page = markup.page()
    page.twotags.append('footer')
    markup.element('footer', case=page.case, parent=page)(class_='footer')
    page.div(class_='container')
    # write user/time for analysis
    if date is None:
        date = datetime.datetime.now().replace(second=0, microsecond=0)
    version = get_versions()['version']
    commit = get_versions()['full-revisionid']
    url = 'https://github.com/gwdetchar/hveto/tree/%s' % commit
    hlink = markup.oneliner.a('Hveto version %s' % version, href=url,
                              target='_blank')
    page.p('Page generated using %s by %s at %s'
           % (hlink, getuser(), date))
    # link to 'about'
    if about is not None:
        page.a('How was this page generated?', href=about)
    page.div.close()  # container
    markup.element('footer', case=page.case, parent=page).close()
    return page


def write_config_html(filepath, format='ini'):
    """Return an HTML-formatted copy of the file with syntax highlighting

    This method attemps to use the `highlight` package to provide a block
    of HTML that can be embedded inside a ``<pre></pre>`` tag.

    Parameters
    ----------
    filepath : `str`
        path of file to format
    format : `str`, optional
        syntax format for this file

    Returns
    -------
    html : `str`
        a formatted block of HTML containing HTML with inline CSS
    """
    highlight = ['highlight', '--out-format', 'html', '--syntax', format,
                 '--inline-css', '--fragment', '--input', filepath]
    try:
        process = subprocess.Popen(highlight, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except OSError:
        with open(filepath, 'r') as fobj:
            return fobj.read()
    else:
        out, err = process.communicate()
        if process.returncode != 0:
            with open(filepath, 'r') as fobj:
                return fobj.read()
        else:
            return out


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
    page : `~glue.markup.page`
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
        page.td(html_link('#hveto-round-%d' % r.n, r.n, target=None,
                          title="Jump to round %d details" % r.n))
        # link name to CIS
        page.td(cis_link(r.winner.name))
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
        page.add(scaffold_plots(plots, nperrow=plotsperrow))
    return page()


def write_round(round):
    """Write the HTML summary for a specific round

    Parameters
    ----------
    round : `HvetoRound`
        the analysis round object

    Returns
    -------
    page : `~glue.markup.page`
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
        link = ' '.join([html_link(
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
    page.add(scaffold_plots(round.plots[:-1], nperrow=4))
    # add significance drop plot at end
    page.div(class_='row')
    page.div(class_='col-sm-12')
    page.add(fancybox_img(round.plots[-1]))
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
    page = markup.page()
    page.h2('Command-line')
    page.pre(' '.join(sys.argv))
    page.h2('Configuration')
    page.pre(write_config_html(configfile))
    return page
