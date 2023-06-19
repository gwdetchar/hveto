# -*- coding: utf-8 -*-

import sys
import os
import glob
import sphinx_bootstrap_theme

from hveto import __version__ as hveto_version

# -- General configuration

# General information about the project.
project = u'Hveto'
copyright = u'2016, Josh Smith'
author = 'Josh Smith, Duncan Macleod, Alex Urban'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = hveto_version
# The full version, including alpha/beta/rc tags.
release = hveto_version

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

# The reST default role (used for this markup: `text`) to use for all
# documents.
default_role = 'obj'

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'default'

# -- Options for HTML output

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'bootstrap'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    'source_link_position': None,
    'navbar_site_name': "Contents",
    'navbar_sidebarrel': True,
    'navbar_pagenav': False,
    'bootswatch_theme': 'united',
}

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = sphinx_bootstrap_theme.get_html_theme_path()

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, maps document names to template names.
html_sidebars = {'**': ['localtoc.html', 'sourcelink.html', 'searchbox.html']}

# Output file base name for HTML help builder.
htmlhelp_basename = 'Hvetodoc'

# Extra files to include
html_css_files = ["css/custom.css"]

# -- Extensions

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'numpydoc',
    'sphinxcontrib.programoutput',
]

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('http://docs.python.org/', None),
    'numpy': ('http://docs.scipy.org/doc/numpy/', None),
    'scipy': ('http://docs.scipy.org/doc/scipy/reference/', None),
    'matplotlib': ('http://matplotlib.sourceforge.net/', None),
    'astropy': ('http://docs.astropy.org/en/stable/', None),
    'gwpy': ('http://gwpy.github.io/docs/stable/', None),
    'gwdetchar': ('http://gwdetchar.readthedocs.io/en/stable', None),
    'gwsumm': ('http://gwsumm.readthedocs.io/en/stable', None),
}

# autosummary
autosummary_generate = True

# numpydoc
# use blockquotes (numpydoc>=0.8 only)
numpydoc_use_blockquotes = True


# -- run sphinx-apidoc automatically
# this is required to have apidoc generated as part of readthedocs builds
# see https://github.com/readthedocs/readthedocs.org/issues/1139

def run_apidoc(_):
    """Call sphinx-apidoc
    """
    from sphinx.ext.apidoc import main as apidoc_main
    curdir = os.path.abspath(os.path.dirname(__file__))
    apidir = os.path.join(curdir, 'api')
    module = os.path.join(curdir, os.path.pardir, 'hveto')
    apidoc_main([module, '--separate', '--force', '--output-dir', apidir])


# -- setup

def setup(app):
    app.connect('builder-inited', run_apidoc)
