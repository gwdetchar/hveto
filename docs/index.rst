=================
Hierarchical Veto
=================

|PyPI version| |Conda version|

|DOI| |License| |Supported Python versions|

Hveto is a package designed for gravitational-wave detector characterisation
and data quality. The algorithm identifies statistically significant
correlations between transient noise events (triggers) in instrumental or
environmental data channels, and those in the calibrated gravitational-wave
strain output. Hveto is a key tool in reducing the noise background in searches
for transient gravitational-wave signals, and was used, for example, during the
detection of the binary black hole signal
`GW150914 <https://www.ligo.caltech.edu/detection>`_.

For full details about the algorithm, please refer to `Smith et al. 2011`_
(Classical and Quantum Gravity).

To get started, simply import the core module:

.. code:: python

   import hveto

------------
Installation
------------

Hveto is best installed with `conda`_:

.. code:: bash

   conda install -c conda-forge hveto

but can also be installed with `pip`_:

.. code:: bash

   python -m pip install hveto

Note, users with `LIGO.ORG` credentials have access to a software
container with a regularly-updated build of Hveto. For more
information please refer to the
`LSCSoft Conda <https://docs.ligo.org/lscsoft/conda/>`_ documentation.

------------
Contributing
------------

All code should follow the Python Style Guide outlined in `PEP 0008`_;
users can use the `flake8`_ package to check their code for style issues
before submitting.

See `the contributions guide`_ for the recommended procedure for
proposing additions/changes.

The Hveto project is hosted on GitHub:

* Issue tickets: https://github.com/gwdetchar/hveto/issues
* Source code: https://github.com/gwdetchar/hveto

License
-------

Hveto is distributed under the `GNU General Public License`_.

.. toctree::
   :maxdepth: 1
   :hidden:

   command-line/index
   api/hveto.config
   api/index

.. _PEP 0008: https://www.python.org/dev/peps/pep-0008/
.. _flake8: http://flake8.pycqa.org
.. _the contributions guide: https://github.com/gwdetchar/hveto/blob/master/CONTRIBUTING.md
.. _conda: https://conda.io
.. _pip: https://pip.pypa.io/en/stable/
.. _Smith et al. 2011: //dx.doi.org/10.1088/0264-9381/28/23/235005
.. _GNU General Public License: https://github.com/gwdetchar/hveto/blob/master/LICENSE

.. |PyPI version| image:: https://badge.fury.io/py/hveto.svg
   :target: http://badge.fury.io/py/hveto
.. |Conda version| image:: https://img.shields.io/conda/vn/conda-forge/hveto.svg
   :target: https://anaconda.org/conda-forge/hveto/
.. |DOI| image:: https://zenodo.org/badge/DOI/10.5281/2584615.svg
   :target: https://doi.org/10.5281/zenodo.2584615
.. |License| image:: https://img.shields.io/pypi/l/hveto.svg
   :target: https://choosealicense.com/licenses/gpl-3.0/
.. |Supported Python versions| image:: https://img.shields.io/pypi/pyversions/hveto.svg
   :target: https://pypi.org/project/hveto/
