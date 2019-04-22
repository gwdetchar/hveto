.. _command-line:

###################
On the command-line
###################

The main interface to the Hveto algorithm is the command-line executable `hveto`.

Basic instructions
==================

For a full explanation of the available command-line arguments and options, you can run

.. command-output:: hveto --help

Detailed instructions
=====================

A few of the command-line options require special formatting, which is detailed
in this section.

`gpsstart` and `gpsend`
---------------------------

Each of the required GPS start and stop times can be given as GPS integers, or as date strings, e.g.

.. code-block:: bash

   hveto 1135641617 1135728017 ...

will produce the same analysis as

.. code-block:: bash

   hveto "Jan 1 2016" "Jan 2 2016" ...

.. note::

   It is important to use quote marks when passing date strings on the command-line.
   This will ensure that the shell passes these to `python` as individual arguments.

   

`-j/--nproc`
--------------

Wall-clock processing time for `hveto` is dominated by two things:

- Reading event files for the auxiliary channels
- Determining the most-significant channel for a given round

Each of these can be sped up by using multiple CPUs on the host machine by
supplying `--nproc X`, where `X` is any integer.

.. warning::

   Beware that using too many CPUs could overload the machine at runtime,
   or otherwise cause problems for yourself and other users.

   You can check how many processors are available with the following unix
   command:

   .. code:: bash

      cat /proc/cpuinfo | grep processor | wc -l

`-p/--primary-cache`
----------------------

This flag should receive a LAL-format cache file (see :mod:`glue.lal` for details).
If needed, you can use `hveto-cache-events` for this purpose (see below).

`-a/--auxiliary-cache`
------------------------

This flag requires a LAL-format cache file (similar to `--primary-cache`),
but with a specific format:

- Each trigger file should contain events for only a single channel
- The cached trigger files should map to their channel as follows:
  if a channel is named `X1:SYS-SUBSYS_NAME`, each filename should start
  `X1-SYS_SUBSYS_NAME` according to the `T050017 <https://dcc.ligo.org/LIGO-T050017>`_
  convention. Additional underscore-delimited components can be given,
  but will not be used to map to the channel.

If needed, `hveto-cache-events` can be used to create this cache (see below).

.. note::

   If `channels` is not given in the `[auxiliary]` section of the
   configuration file, it will be populated from the unique list of channels
   parsed from the `--auxiliary-cache`.

Caching trigger events
======================

The `hveto-cache-events` utility can be used to save both gravitational-wave
and auxiliary channel triggers:

.. command-output:: hveto-cache-events --help

Tracing event triggers
======================

The `hveto-trace` utility can be used to determine whether event triggers
are vetoed by a given `hveto` run:

.. command-output:: hveto-trace --help
