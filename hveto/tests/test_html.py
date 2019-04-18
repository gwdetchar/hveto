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
import shutil

import pytest

from gwdetchar.utils import parse_html

from .. import html

BANNER = """<div class="page-header" role="banner">
<h1>L1 HierarchicalVeto</h1>
<h3>0-100</h3>
</div>"""

NAVBAR = """<header class="navbar navbar-fixed-top navbar-h1">
<div class="container">
<div class="navbar-header">
<button class="navbar-toggle" data-toggle="collapse" type="button" data-target=".navbar-collapse">
<span class="icon-bar"></span>
<span class="icon-bar"></span>
<span class="icon-bar"></span>
</button>
<div class="navbar-brand">H1</div>
<div class="navbar-brand">Hveto</div>
<div class="btn-group pull-right ifo-links">
<a class="navbar-brand dropdown-toggle" href="#" data-toggle="dropdown">
Links
<b class="caret"></b>
</a>
<ul class="dropdown-menu">
<li class="dropdown-header">Internal</li>
<li>
<a href="about">About this page</a>
</li>
<li class="divider"></li>
<li class="dropdown-header">External</li>
<li>
<a href="https://ldas-jobs.ligo-wa.caltech.edu/~detchar/summary/day/19800106" target="_blank">LHO Summary Pages</a>
</li>
<li>
<a href="https://alog.ligo-wa.caltech.edu/aLOG" target="_blank">LHO Logbook</a>
</li>
</ul>
</div>
</div>
<nav class="collapse navbar-collapse">
<ul class="nav navbar-nav">
<li>
<a href="#">Summary</a>
</li>
<li class="dropdown">
<a href="#" class="dropdown-toggle" data-toggle="dropdown">
Rounds
<b class="caret"></b>
</a>
<ul class="dropdown-menu">
<li>
<a href="#hveto-round-1">1: H1:TEST-STRAIN</a>
</li>
</ul>
</li>
</ul>
</nav>
</div>
</header>"""  # noqa: E501


# -- unit tests ---------------------------------------------------------------

def test_banner():
    # test simple content
    out = html.banner('L1', 0, 100)
    assert parse_html(str(out)) == parse_html(BANNER)


def test_navbar():
    # test simple content
    out = html.navbar('H1', 0, ['H1:TEST-STRAIN'])
    assert parse_html(str(out)) == parse_html(NAVBAR)


@pytest.mark.parametrize('args, kwargs, result', [
    (('Key', 'Value'), {}, '<p><b>Key</b>: Value</p>'),
    (('Key', 'Value'), {'class': 'hveto', 'id_': 'test-case'},
     '<p id="test-case" class="hveto"><b>Key</b>: Value</p>'),
])
def test_bold_param(args, kwargs, result):
    h1 = parse_html(html.bold_param(*args, **kwargs))
    h2 = parse_html(result)
    assert h1 == h2


# -- end-to-end tests ---------------------------------------------------------

def test_write_hveto_page(tmpdir):
    os.chdir(str(tmpdir))
    config = 'test.ini'
    with open(config, 'w') as fobj:
        fobj.write('[test]\nchannel = X1:TEST')
    htmlv = {
        'title': 'test',
        'base': 'test',
        'config': config,
    }
    html.write_hveto_page('L1', 0, 86400, [], [], **htmlv)
    shutil.rmtree(str(tmpdir), ignore_errors=True)


def test_write_null_page(tmpdir):
    os.chdir(str(tmpdir))
    html.write_null_page('L1', 0, 86400, 'test', 'info')
    shutil.rmtree(str(tmpdir), ignore_errors=True)
