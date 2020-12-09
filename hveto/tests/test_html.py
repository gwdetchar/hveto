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
<h1 class="pb-2 mt-3 mb-2 border-bottom">L1 HierarchicalVeto</h1>
<h3 class="mt-3">0-100</h3>
</div>"""

NAVBAR = """<nav class="navbar fixed-top navbar-expand-md navbar-h1 shadow-sm">
<div class="container-fluid">
<div class="navbar-brand border border-white rounded">H1 Hveto</div>
<button class="navbar-toggler navbar-toggler-right" type="button" data-toggle="collapse" data-target=".navbar-collapse">
<span class="navbar-toggler-icon"></span>
</button>
<div class="collapse navbar-collapse justify-content-between">
<ul class="nav navbar-nav mr-auto">
<li class="nav-item">
<a href="#" class="nav-link">Summary</a>
</li>
<li class="nav-item dropdown">
<a href="#" class="nav-link dropdown-toggle" role="button" data-toggle="dropdown">Rounds</a>
<div class="dropdown-menu dropdown-1-col shadow">
<a href="#hveto-round-1" class="dropdown-item">1: H1:TEST-STRAIN</a>
</div>
</li>
</ul>
<ul class="nav navbar-nav">
<li class="nav-item dropdown">
<a class="nav-link dropdown-toggle" href="#" role="button" data-toggle="dropdown">Links</a>
<div class="dropdown-menu dropdown-menu-right shadow">
<h6 class="dropdown-header">Internal</h6>
<a href="about" class="dropdown-item">About this page</a>
<div class="dropdown-divider"></div>
<h6 class="dropdown-header">External</h6>
<a href="https://ldas-jobs.ligo-wa.caltech.edu/~detchar/summary/day/19800106" class="dropdown-item" target="_blank">LHO Summary Pages</a>
<a href="https://alog.ligo-wa.caltech.edu/aLOG" class="dropdown-item" target="_blank">LHO Logbook</a>
</div>
</li>
</ul>
</div>
</div>
</nav>"""  # noqa: E501


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
