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

"""Tests for `hveto.html`
"""

import os
import tempfile
import shutil
import time
import datetime
from getpass import getuser

import pytest

from matplotlib import use
use('agg')  # nopep8

from .. import html
from .._version import get_versions
from ..plot import FancyPlot

VERSION = get_versions()['version']
COMMIT = get_versions()['full-revisionid']

HTML_INIT = """<!DOCTYPE HTML>
<html lang="en">
<head>
<base href="{base}" />
<link media="all" href="//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" type="text/css" rel="stylesheet" />
<link media="all" href="//cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.css" type="text/css" rel="stylesheet" />
<link media="all" href="//fonts.googleapis.com/css?family=Lato:300,700" type="text/css" rel="stylesheet" />
<link media="all" href="{css}" type="text/css" rel="stylesheet" />
<script src="//code.jquery.com/jquery-1.11.2.min.js" type="text/javascript"></script>
<script src="//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js" type="text/javascript"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.js" type="text/javascript"></script>
<script src="{js}" type="text/javascript"></script>
</head>
<body>
<div class="container">
<div class="page-header" role="banner">
<h1>L1 HierarchicalVeto</h1>
<h3>0-100</h3>
</div>
</div>
<div class="container">
</body>
</html>"""

HTML_FOOTER = """<footer class="footer">
<div class="container">
<p>Page generated using <a href="https://github.com/gwdetchar/hveto/tree/%s" target="_blank">Hveto version %s</a> by {user} at {date}</p>
</div>
</footer>""" % (COMMIT, VERSION)

HTML_CLOSE = """</div>
%s
</body>
</html>""" % HTML_FOOTER

TEMPDIR = None
_OLDPWD = None


def setup_module():
    global TEMPDIR, _OLDPWD
    TEMPDIR = tempfile.mkdtemp()
    _OLDPWD = os.getcwd()
    os.chdir(TEMPDIR)


def teardown_module():
    os.chdir(_OLDPWD)
    if os.path.isdir(TEMPDIR):
        shutil.rmtree(TEMPDIR)


def test_init_page():
    # test simple content
    out = html.init_page('L1', 0, 100, base=TEMPDIR)
    css = os.path.join(os.path.curdir, 'static', 'hveto.css')
    js = os.path.join(os.path.curdir, 'static', 'hveto.js')
    assert str(out) == HTML_INIT.format(base=TEMPDIR, css=css, js=js)


def test_write_static_files():
    # test files get written
    static = os.path.join(TEMPDIR, 'static')
    html.write_static_files(static)
    for ext in ['css', 'js']:
        assert os.path.isfile(os.path.join(static, 'hveto.%s' % ext))

    # test files don't get written again
    now = time.time()
    html.write_static_files(static)
    for ext in ['css', 'js']:
        f = os.path.join(static, 'hveto.%s' % ext)
        assert os.path.getmtime(f) < now

    # check content
    for ext, content in zip(
            ['css', 'js'], [html.HVETO_CSS, html.HVETO_JS]):
        f = os.path.join(static, 'hveto.%s' % ext)
        with open(f, 'r') as fp:
            assert fp.read() == content


def test_close_page():
    # test simple content
    target = os.path.join(TEMPDIR, 'test.html')
    date = datetime.datetime.now()
    page = html.close_page(html.markup.page(), target, date=date)
    assert str(page) == HTML_CLOSE.format(user=getuser(), date=str(date))
    assert os.path.isfile(target)
    with open(target, 'r') as fp:
        assert fp.read() == str(page)


@pytest.mark.parametrize('args, kwargs, result', [
    (('Key', 'Value'), {}, '<p><b>Key</b>: Value</p>'),
    (('Key', 'Value'), {'class': 'hveto', 'id_': 'test-case'},
     '<p id="test-case" class="hveto"><b>Key</b>: Value</p>'),
])
def test_bold_param(args, kwargs, result):
    assert html.bold_param(*args, **kwargs) == result


@pytest.mark.parametrize('args, kwargs, result', [
    (('test.html', 'Test link'), {},
     '<a href="test.html" target="_blank">Test link</a>'),
    (('test.html', 'Test link'), {'class_': 'test-case'},
     '<a class="test-case" href="test.html" target="_blank">Test link</a>'),
])
def test_html_link(args, kwargs, result):
    assert html.html_link(*args, **kwargs) == result


def test_cis_link():
    assert html.cis_link('X1:TEST-CHANNEL') == (
        '<a style="font-family: Monaco, &quot;Courier New&quot;, '
        'monospace;" href="https://cis.ligo.org/channel/byname/'
        'X1:TEST-CHANNEL" target="_blank" title="CIS entry for '
        'X1:TEST-CHANNEL">X1:TEST-CHANNEL</a>'
    )


def test_fancybox_img():
    img = FancyPlot('test.png')
    out = html.fancybox_img(img)
    assert out == (
        '<a class="fancybox" href="test.png" target="_blank" '
        'data-fancybox-group="hveto-image" title="test.png">\n'
        '<img class="img-responsive" alt="test.png" src="test.png" />'
        '\n</a>'
    )


def test_scaffold_plots():
    assert html.scaffold_plots([FancyPlot('plot1.png'),
                                FancyPlot('plot2.png')]) == (
        '<div class="row">\n'
        '<div class="col-sm-6">\n'
        '<a class="fancybox" href="plot1.png" target="_blank" '
            'data-fancybox-group="hveto-image" title="plot1.png">\n'
        '<img class="img-responsive" alt="plot1.png" '
            'src="plot1.png" />\n'
        '</a>\n'
        '</div>\n'
        '<div class="col-sm-6">\n'
        '<a class="fancybox" href="plot2.png" target="_blank" '
        'data-fancybox-group="hveto-image" title="plot2.png">\n'
        '<img class="img-responsive" alt="plot2.png" '
            'src="plot2.png" />\n'
        '</a>\n'
        '</div>\n'
        '</div>'
    )


def test_write_footer():
    date = datetime.datetime.now()
    out = html.write_footer(date=date)
    assert str(out) == HTML_FOOTER.format(user=getuser(), date=date)
