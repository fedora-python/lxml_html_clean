Welcome to lxml_html_clean's documentation!
===========================================

Motivation
----------

This project was initially a part of `lxml <https://github.com/lxml/lxml>`_. Because HTML cleaner is designed as blocklist-based,
many reports about possible security vulnerabilities were filed for lxml and that make the project problematic for
security-sensitive environments. Therefore we decided to extract the problematic part to a separate project.

**Important**: the HTML Cleaner in ``lxml_html_clean`` is **not** considered appropriate **for security sensitive environments**.
See e.g. `bleach <https://pypi.org/project/bleach/>`_ for an alternative.

This project uses functions from Python's ``urllib.parse`` for URL parsing which **do not validate inputs**.
For more information on potential security risks, refer to the
`URL parsing security <https://docs.python.org/3/library/urllib.parse.html#url-parsing-security>`_ documentation.
A maliciously crafted URL could potentially bypass the allowed hosts check in ``Cleaner``.

Security
--------

For discussions regarding security-related issues or any sensitive reports, please contact us privately.
You can reach out to lbalhar(at)redhat.com or frenzy.madness(at)gmail.com to ensure your concerns
are addressed confidentially and securely.

Installation
------------

You can install this project directly via ``pip install lxml_html_clean`` or soon as an extra of lxml
via ``pip install lxml[html_clean]``. Both ways installs this project together with lxml itself.

Usage
=====

.. toctree::
   :maxdepth: 2

   usage

API
===

.. toctree::
   :maxdepth: 2

   lxml_html_clean

Changelog
=========

.. toctree::
   :maxdepth: 2

   changes

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
