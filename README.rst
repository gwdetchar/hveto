HVeto is a python implementation of the HierarchicalVeto algorithm. It is
a package designed for for gravitational-wave detector characterisation and
data quality.

|PyPI version| |DOI| |License| |Supported Python versions|

|Build Status| |Coverage Status|

------
Method
------

The HVeto algorithm is fully described in `Smith et al. 2011`_
(Classical and Quantum Gravity). `Documentation`_ for running HVeto
is also available, but requires LIGO.ORG credentials.

------------
Installation
------------

HVeto is best installed with `conda`_:

.. code:: bash

   conda install -c conda-forge hveto

but can also be installed with `pip`_:

.. code:: bash

   python -m pip install hveto

------------
Contributing
------------

All code should follow the Python Style Guide outlined in `PEP 0008`_;
users can use the `pep8`_ package to check their code for style issues
before submitting.

See `the contributions guide`_ for the recommended procedure for
proposing additions/changes.

.. _PEP 0008: https://www.python.org/dev/peps/pep-0008/
.. _pep8: https://pypi.python.org/pypi/pep8
.. _the contributions guide: https://github.com/gwdetchar/hveto/blob/master/CONTRIBUTING.md
.. _conda: https://conda.io
.. _pip: https://pip.pypa.io/en/stable/
.. _Smith et al. 2011: //dx.doi.org/10.1088/0264-9381/28/23/235005
.. _Documentation: https://ldas-jobs.ligo.caltech.edu/~duncan.macleod/hveto/latest/

.. |PyPI version| image:: https://badge.fury.io/py/hveto.svg
   :target: http://badge.fury.io/py/hveto
.. |DOI| image:: https://zenodo.org/badge/DOI/10.5281/2584615.svg
   :target: https://doi.org/10.5281/zenodo.2584615
.. |License| image:: https://img.shields.io/pypi/l/hveto.svg
   :target: https://choosealicense.com/licenses/gpl-3.0/
.. |Supported Python versions| image:: https://img.shields.io/pypi/pyversions/hveto.svg
   :target: https://pypi.org/project/hveto/
.. |Build Status| image:: https://travis-ci.org/gwdetchar/hveto.svg?branch=master
   :target: https://travis-ci.org/gwdetchar/hveto
.. |Coverage Status| image:: https://coveralls.io/repos/github/gwdetchar/hveto/badge.svg?branch=master
   :target: https://coveralls.io/github/gwdetchar/hveto?branch=master
