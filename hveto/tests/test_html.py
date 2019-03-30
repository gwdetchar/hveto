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

BANNER = """<div class="container">
<div class="page-header" role="banner">
<h1>L1 HierarchicalVeto</h1>
<h3>0-100</h3>
</div>
</div>"""


# -- unit tests ---------------------------------------------------------------

def test_banner():
    # test simple content
    out = html.banner('L1', 0, 100)
    assert parse_html(str(out)) == parse_html(BANNER)


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
