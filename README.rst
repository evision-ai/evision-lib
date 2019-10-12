========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |
        |
    * - package
      - | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/evision-lib/badge/?style=flat
    :target: https://readthedocs.org/projects/evision-lib
    :alt: Documentation Status

.. |commits-since| image:: https://img.shields.io/github/commits-since/evision-ai/evision-lib/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/evision-ai/evision-lib/compare/v0.1.0...master



.. end-badges

eVision Common Python Library

Installation
============

::

    pip install evision-lib

You can also install the in-development version with::

    pip install https://github.com/evision-ai/evision-lib/archive/master.zip


Documentation
=============


https://evision-lib.readthedocs.io/


Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
