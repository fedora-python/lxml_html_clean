=========================
lxml_html_clean changelog
=========================


Unreleased
==========

0.3.0 (2024-10-09)
==================

Features added
--------------

* Parsing of URL addresses has been enhanced and Cleaner removes ambiguous URLs.

0.2.2 (2024-08-30)
==================

Bugs fixed
----------

* sdist now includes all test files and changelog.

0.2.1 (2024-08-29)
==================

Bugs fixed
----------

* Memory efficiency is now much better for HTML pages where cleaner removes
  a lot of elements. (#14)


0.2.0 (2024-07-29)
==================

Features added
--------------

* ASCII control characters (except HT, VT, CR and LF) are now removed
  from string inputs before they're parsed by lxml/libxml2.

0.1.1 (2024-04-05)
==================

Bugs fixed
----------

* Regular expresion for image data URLs now supports multiple data
  URLs on a single line.


0.1.0 (2024-02-26)
==================

First official release of the split project.


Relevant changes from lxml project before the split
===================================================

This part contains releases of lxml project containing important changes
related to HTML Cleaner functionalities.

5.1.0 (2024-01-05)
==================

Bugs fixed
----------

* The HTML ``Cleaner()`` interpreted an accidentally provided string parameter
  for the ``host_whitelist`` as list of characters and silently failed to reject any hosts.
  Passing a non-collection is now rejected.


4.9.3 (2023-07-05)
==================

Bugs fixed
----------

* A memory leak in ``lxml.html.clean`` was resolved by switching to Cython 0.29.34+.

* URL checking in the HTML cleaner was improved.
  Patch by Tim McCormack.


4.6.5 (2021-12-12)
==================

Bugs fixed
----------

* A vulnerability (GHSL-2021-1038) in the HTML cleaner allowed sneaking script
  content through SVG images (CVE-2021-43818).

* A vulnerability (GHSL-2021-1037) in the HTML cleaner allowed sneaking script
  content through CSS imports and other crafted constructs (CVE-2021-43818).


4.6.3 (2021-03-21)
==================

Bugs fixed
----------

* A vulnerability (CVE-2021-28957) was discovered in the HTML Cleaner by Kevin Chung,
  which allowed JavaScript to pass through.  The cleaner now removes the HTML5
  ``formaction`` attribute.


4.6.2 (2020-11-26)
==================

Bugs fixed
----------

* A vulnerability (CVE-2020-27783) was discovered in the HTML Cleaner by Yaniv Nizry,
  which allowed JavaScript to pass through.  The cleaner now removes more sneaky
  "style" content.


4.6.1 (2020-10-18)
==================

Bugs fixed
----------

* A vulnerability was discovered in the HTML Cleaner by Yaniv Nizry, which allowed
  JavaScript to pass through.  The cleaner now removes more sneaky "style" content.


4.5.2 (2020-07-09)
==================

Bugs fixed
----------

* ``Cleaner()`` now validates that only known configuration options can be set.

* ``Cleaner.clean_html()`` discarded comments and PIs regardless of the
  corresponding configuration option, if ``remove_unknown_tags`` was set.


4.2.5 (2018-09-09)
==================

Bugs fixed
----------

* Javascript URLs that used URL escaping were not removed by the HTML cleaner.
  Security problem found by Omar Eissa.  (CVE-2018-19787)


4.0.0 (2017-09-17)
==================

Features added
--------------

* The modules ``lxml.builder``, ``lxml.html.diff`` and ``lxml.html.clean``
  are also compiled using Cython in order to speed them up.
