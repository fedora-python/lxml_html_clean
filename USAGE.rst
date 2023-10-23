Cleaning up HTML
================

The module ``lxml.html.clean`` provides a ``Cleaner`` class for cleaning up
HTML pages.  It supports removing embedded or script content, special tags,
CSS style annotations and much more.

Note: the HTML Cleaner in ``lxml.html.clean`` is **not** considered
appropriate **for security sensitive environments**.
See e.g. `bleach <https://pypi.org/project/bleach/>`_ for an alternative.

Say, you have an overburdened web page from a hideous source which contains
lots of content that upsets browsers and tries to run unnecessary code on the
client side:

.. sourcecode:: pycon

    >>> html = '''\
    ... <html>
    ...  <head>
    ...    <script type="text/javascript" src="evil-site"></script>
    ...    <link rel="alternate" type="text/rss" src="evil-rss">
    ...    <style>
    ...      body {background-image: url(javascript:do_evil)};
    ...      div {color: expression(evil)};
    ...    </style>
    ...  </head>
    ...  <body onload="evil_function()">
    ...    <!-- I am interpreted for EVIL! -->
    ...    <a href="javascript:evil_function()">a link</a>
    ...    <a href="#" onclick="evil_function()">another link</a>
    ...    <p onclick="evil_function()">a paragraph</p>
    ...    <div style="display: none">secret EVIL!</div>
    ...    <object> of EVIL! </object>
    ...    <iframe src="evil-site"></iframe>
    ...    <form action="evil-site">
    ...      Password: <input type="password" name="password">
    ...    </form>
    ...    <blink>annoying EVIL!</blink>
    ...    <a href="evil-site">spam spam SPAM!</a>
    ...    <image src="evil!">
    ...  </body>
    ... </html>'''

To remove the all superfluous content from this unparsed document, use the
``clean_html`` function:

.. sourcecode:: pycon

    >>> from lxml.html.clean import clean_html
    >>> print clean_html(html)
    <div><style>/* deleted */</style><body>
       
       <a href="">a link</a>
       <a href="#">another link</a>
       <p>a paragraph</p>
       <div>secret EVIL!</div>
        of EVIL! 
                                                                                                       
                                                                                                       
         Password:                                                                                     
       annoying EVIL!<a href="evil-site">spam spam SPAM!</a>                                           
       <img src="evil!"></body></div>   

The ``Cleaner`` class supports several keyword arguments to control exactly
which content is removed:

.. sourcecode:: pycon

    >>> from lxml.html.clean import Cleaner

    >>> cleaner = Cleaner(page_structure=False, links=False)
    >>> print cleaner.clean_html(html)
    <html>
      <head>
        <link rel="alternate" src="evil-rss" type="text/rss">
        <style>/* deleted */</style>
      </head>
      <body>
        <a href="">a link</a>
        <a href="#">another link</a>
        <p>a paragraph</p>
        <div>secret EVIL!</div>
        of EVIL!
        Password:
        annoying EVIL!
        <a href="evil-site">spam spam SPAM!</a>
        <img src="evil!">
      </body>
    </html>

    >>> cleaner = Cleaner(style=True, links=True, add_nofollow=True,
    ...                   page_structure=False, safe_attrs_only=False)
    
    >>> print cleaner.clean_html(html)
    <html>
      <head>
      </head>
      <body>
        <a href="">a link</a>
        <a href="#">another link</a>
        <p>a paragraph</p>
        <div>secret EVIL!</div>
        of EVIL!
        Password:
        annoying EVIL!
        <a href="evil-site" rel="nofollow">spam spam SPAM!</a>
        <img src="evil!">
      </body>
    </html>

You can also whitelist some otherwise dangerous content with
``Cleaner(host_whitelist=['www.youtube.com'])``, which would allow
embedded media from YouTube, while still filtering out embedded media
from other sites.

See the docstring of ``Cleaner`` for the details of what can be
cleaned.


autolink
--------

In addition to cleaning up malicious HTML, ``lxml.html.clean``
contains functions to do other things to your HTML.  This includes
autolinking::

   autolink(doc, ...)

   autolink_html(html, ...)

This finds anything that looks like a link (e.g.,
``http://example.com``) in the *text* of an HTML document, and
turns it into an anchor.  It avoids making bad links.

Links in the elements ``<textarea>``, ``<pre>``, ``<code>``,
anything in the head of the document.  You can pass in a list of
elements to avoid in ``avoid_elements=['textarea', ...]``.

Links to some hosts can be avoided.  By default links to
``localhost*``, ``example.*`` and ``127.0.0.1`` are not
autolinked.  Pass in ``avoid_hosts=[list_of_regexes]`` to control
this.

Elements with the ``nolink`` CSS class are not autolinked.  Pass
in ``avoid_classes=['code', ...]`` to control this.

The ``autolink_html()`` version of the function parses the HTML
string first, and returns a string.


wordwrap
--------

You can also wrap long words in your html::

   word_break(doc, max_width=40, ...)

   word_break_html(html, ...)

This finds any long words in the text of the document and inserts
``&#8203;`` in the document (which is the Unicode zero-width space).

This avoids the elements ``<pre>``, ``<textarea>``, and ``<code>``.
You can control this with ``avoid_elements=['textarea', ...]``.

It also avoids elements with the CSS class ``nobreak``.  You can
control this with ``avoid_classes=['code', ...]``.

Lastly you can control the character that is inserted with
``break_character=u'\u200b'``.  However, you cannot insert markup,
only text.

``word_break_html(html)`` parses the HTML document and returns a
string.
