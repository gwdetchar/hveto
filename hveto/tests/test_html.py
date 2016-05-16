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

import os.path
import tempfile
import shutil
import time
import datetime
from getpass import getuser

from hveto import html
from hveto._version import get_versions

from common import unittest

VERSION = get_versions()['version']
COMMIT = get_versions()['full-revisionid']

HTML_INIT = """<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01 Transitional//EN'>
<html lang="en">
<head>
<link media="all" href="//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css" type="text/css" rel="stylesheet" />
<link media="all" href="//cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.css" type="text/css" rel="stylesheet" />
<link media="all" href="//fonts.googleapis.com/css?family=Lato:300,700" type="text/css" rel="stylesheet" />
<link media="all" href="{css}" type="text/css" rel="stylesheet" />
<script src="//code.jquery.com/jquery-1.11.2.min.js" type="text/javascript"></script>
<script src="//maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js" type="text/javascript"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/fancybox/2.1.5/jquery.fancybox.min.js" type="text/javascript"></script>
<script src="{js}" type="text/javascript"></script>
<base href="{base}" />
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
<p>Page generated using <a href="https://github.com/hveto/hveto/tree/%s" target="_blank">Hveto version %s</a> by {user} at {date}</p>
</footer>""" % (COMMIT, VERSION)

HTML_CLOSE = """</div>
%s
</body>
</html>""" % HTML_FOOTER

class HtmlTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.isdir(self.tempdir):
            shutil.rmtree(self.tempdir)

    def test_init_page(self):
        # test simple content
        out = html.init_page('L1', 0, 100, base=self.tempdir)
        css = os.path.join(self.tempdir, 'static', 'hveto.css')
        js = os.path.join(self.tempdir, 'static', 'hveto.js')
        self.assertEqual(str(out),
                         HTML_INIT.format(base=self.tempdir, css=css, js=js))

    def test_write_static_files(self):
        # test files get written
        static = os.path.join(self.tempdir, 'static')
        files = html.write_static_files(static)
        for ext in ['css', 'js']:
            self.assertTrue(os.path.isfile(
                os.path.join(static, 'hveto.%s' % ext)))
        now = time.time()
        # test files don't get written again
        html.write_static_files(static)
        for ext in ['css', 'js']:
            f = os.path.join(static, 'hveto.%s' % ext)
            self.assertLess(os.path.getmtime(f), now)
        # check content
        for ext, content in zip(
                ['css', 'js'], [html.HVETO_CSS, html.HVETO_JS]):
            f = os.path.join(static, 'hveto.%s' % ext)
            with open(f, 'r') as fp:
                self.assertEqual(fp.read(), content)

    def test_close_page(self):
        # test simple content
        target = os.path.join(self.tempdir, 'test.html')
        date = datetime.datetime.now()
        page = html.close_page(html.markup.page(), target, date=date)
        self.assertEqual(str(page),
                         HTML_CLOSE.format(user=getuser(), date=str(date)))
        self.assertTrue(os.path.isfile(target))
        with open(target, 'r') as fp:
            self.assertEqual(fp.read(), str(page))

    def test_bold_param(self):
        out = html.bold_param('Key', 'Value')
        self.assertEqual(out, '<p><b>Key</b>: Value</p>')
        out = html.bold_param('Key', 'Value', class_='hveto', id_='test-case')
        self.assertEqual(
            out, '<p class="hveto" id="test-case"><b>Key</b>: Value</p>')

    def test_html_link(self):
        out = html.html_link('test.html', 'Test link')
        self.assertEqual(
            out, '<a href="test.html" target="_blank">Test link</a>')
        out = html.html_link('test.html', 'Test link', class_='test-case')
        self.assertEqual(out, '<a class="test-case" href="test.html" '
                              'target="_blank">Test link</a>')

    def test_cis_link(self):
        out = html.cis_link('X1:TEST-CHANNEL')
        self.assertEqual(
            out, '<a style="font-family: Monaco, &quot;Courier New&quot;, '
                 'monospace;" href="https://cis.ligo.org/channel/byname/'
                 'X1:TEST-CHANNEL" target="_blank" title="CIS entry for '
                 'X1:TEST-CHANNEL">X1:TEST-CHANNEL</a>')

    def test_fancybox_img(self):
        out = html.fancybox_img('test.png')
        self.assertEqual(
            out, '<a class="fancybox" href="test.png" target="_blank" '
                 'rel="hveto-image" title="test.png">\n'
                 '<img class="img-responsive" alt="test.png" src="test.png" />'
                 '\n</a>')

    def test_scaffold_plots(self):
        out = html.scaffold_plots(['plot1.png', 'plot2.png'])
        self.assertEqual(
            out, '<div class="row">\n'
                 '<div class="col-sm-6">\n'
                 '<a class="fancybox" href="plot1.png" target="_blank" '
                     'rel="hveto-image" title="plot1.png">\n'
                 '<img class="img-responsive" alt="plot1.png" '
                     'src="plot1.png" />\n'
                 '</a>\n'
                 '</div>\n'
                 '<div class="col-sm-6">\n'
                 '<a class="fancybox" href="plot2.png" target="_blank" '
                 'rel="hveto-image" title="plot2.png">\n'
                 '<img class="img-responsive" alt="plot2.png" '
                     'src="plot2.png" />\n'
                 '</a>\n'
                 '</div>\n'
                 '</div>')

    def test_write_footer(self):
        date = datetime.datetime.now()
        out = html.write_footer(date=date)
        self.assertEqual(str(out),
                         HTML_FOOTER.format(user=getuser(), date=date))
