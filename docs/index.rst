.. Hveto documentation master file, created by
   sphinx-quickstart on Thu Apr 21 14:05:08 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Hveto's documentation!
=================================

The HierarchichalVeto is an algorithm to identify statistically-significant correlations between transient noise events (triggers) in instrumental or environment data channels and those in the main calibrated gravitational-wave strain output for a ground-based laser interferometer gravitational-wave detector.
It is a key tool in reducing the noise background in searches for transient gravitational-wave signals, and was used during the detection of the binary black hole signal `GW150914 <https://www.ligo.caltech.edu/detection>`_.

For full details see `Smith et al. (Classical and Quantum Gravity, 2011) <https://iopscience.iop.org/article/10.1088/0264-9381/28/23/235005>`_

Installing Hveto
----------------

The easiest method to install hveto is using `pip <https://pip.pypa.io/en/stable/>`_ directly from the `GitHub repository <https://github.com/hveto/hveto.git>`_:

.. code-block:: bash

   $ pip install git+https://github.com/hveto/hveto.git

How to run Hveto
----------------

The main product of this package is the command-line executable `hveto`, which runs an end-to-end search for statistical coincidences, and produces a list of viable data-quality flags that can be used as vetoes in a search, as well as an HTML summary.

To run an analysis:

.. code-block:: bash

   $ hveto <gpsstart> <gpsend> --config-file ./my-config-file.ini

where ``<gpsstart>`` and ``<gpsend>`` are the start and stop GPS times of the analysis period, and ``./my-config-file.ini`` is the path of your configuration file. Strictly speaking the configuration file is optional, but is highly recommend if you want to have any control over your analysis.

For a full list of command-line argument and options, run

.. code-block:: bash

   $ hveto --help

For more details see :ref:`command-line`.

Package documentation
---------------------

Please consult these pages for more details on using Hveto:

.. toctree::
   :maxdepth: 1

   command-line/index
   api/hveto.config

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
