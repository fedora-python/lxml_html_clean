import base64
import gzip
import io
import unittest
import warnings

import lxml.html
from lxml_html_clean import AmbiguousURLWarning, Cleaner, clean_html, LXMLHTMLCleanWarning
from .utils import peak_memory_usage


class CleanerTest(unittest.TestCase):
    def test_allow_tags(self):
        html = """
            <html>
            <head>
            </head>
            <body>
            <p>some text</p>
            <table>
            <tr>
            <td>hello</td><td>world</td>
            </tr>
            <tr>
            <td>hello</td><td>world</td>
            </tr>
            </table>
            <img>
            </body>
            </html>
            """

        html_root = lxml.html.document_fromstring(html)
        cleaner = Cleaner(
            remove_unknown_tags = False,
            allow_tags = ['table', 'tr', 'td'])
        result = cleaner.clean_html(html_root)

        self.assertEqual(12-5+1, len(list(result.iter())))

    def test_allow_and_remove(self):
        with self.assertRaises(ValueError):
            Cleaner(allow_tags=['a'], remove_unknown_tags=True)

    def test_remove_unknown_tags(self):
        html = """<div><bun>lettuce, tomato, veggie patty</bun></div>"""
        clean_html = """<div>lettuce, tomato, veggie patty</div>"""
        cleaner = Cleaner(remove_unknown_tags=True)
        result = cleaner.clean_html(html)
        self.assertEqual(
            result,
            clean_html,
            msg="Unknown tags not removed. Got: %s" % result,
        )

    def test_safe_attrs_included(self):
        html = """<p><span style="color: #00ffff;">Cyan</span></p>"""

        safe_attrs=set(lxml.html.defs.safe_attrs)
        safe_attrs.add('style')

        cleaner = Cleaner(
            safe_attrs_only=True,
            safe_attrs=safe_attrs)
        result = cleaner.clean_html(html)

        self.assertEqual(html, result)

    def test_safe_attrs_excluded(self):
        html = """<p><span style="color: #00ffff;">Cyan</span></p>"""
        expected = """<p><span>Cyan</span></p>"""

        safe_attrs=set()

        cleaner = Cleaner(
            safe_attrs_only=True,
            safe_attrs=safe_attrs)
        result = cleaner.clean_html(html)

        self.assertEqual(expected, result)

    def test_clean_invalid_root_tag(self):
        # only testing that cleaning with invalid root tags works at all
        s = lxml.html.fromstring('parent <invalid tag>child</another>')
        self.assertEqual('parent child', clean_html(s).text_content())

        s = lxml.html.fromstring('<invalid tag>child</another>')
        self.assertEqual('child', clean_html(s).text_content())

    def test_clean_with_comments(self):
        html = """<p><span style="color: #00ffff;">Cy<!-- xx -->an</span><!-- XXX --></p>"""
        s = lxml.html.fragment_fromstring(html)

        self.assertEqual(
            b'<p><span>Cyan</span></p>',
            lxml.html.tostring(clean_html(s)))
        self.assertEqual(
            '<p><span>Cyan</span></p>',
            clean_html(html))

        cleaner = Cleaner(comments=False)
        result = cleaner.clean_html(s)
        self.assertEqual(
            b'<p><span>Cy<!-- xx -->an</span><!-- XXX --></p>',
            lxml.html.tostring(result))
        self.assertEqual(
            '<p><span>Cy<!-- xx -->an</span><!-- XXX --></p>',
            cleaner.clean_html(html))

    def test_sneaky_noscript_in_style(self):
        # This gets parsed as <noscript> -> <style>"...</noscript>..."</style>
        # thus passing the </noscript> through into the output.
        html = '<noscript><style><a title="</noscript><img src=x onerror=alert(1)>">'
        s = lxml.html.fragment_fromstring(html)

        self.assertEqual(
            b'<noscript><style>/* deleted */</style></noscript>',
            lxml.html.tostring(clean_html(s)))

    def test_sneaky_js_in_math_style(self):
        # This gets parsed as <math> -> <style>"..."</style>
        # thus passing any tag/script/whatever content through into the output.
        html = '<math><style><img src=x onerror=alert(1)></style></math>'
        s = lxml.html.fragment_fromstring(html)

        self.assertEqual(
            b'<math><style>/* deleted */</style></math>',
            lxml.html.tostring(clean_html(s)))

    def test_sneaky_js_in_style_comment_math_svg(self):
        for tag in "svg", "math":
            html = f'<{tag}><style>p {{color: red;}}/*<img src onerror=alert(origin)>*/h2 {{color: blue;}}</style></{tag}>'
            s = lxml.html.fragment_fromstring(html)

            expected = f'<{tag}><style>p {{color: red;}}/* deleted */h2 {{color: blue;}}</style></{tag}>'.encode()

            self.assertEqual(
                expected,
                lxml.html.tostring(clean_html(s)))

    def test_sneaky_js_in_style_comment_noscript(self):
        html = '<noscript><style>p {{color: red;}}/*</noscript><img src onerror=alert(origin)>*/h2 {{color: blue;}}</style></noscript>'
        s = lxml.html.fragment_fromstring(html)

        self.assertEqual(
            b'<noscript><style>p {{color: red;}}/* deleted */h2 {{color: blue;}}</style></noscript>',
            lxml.html.tostring(clean_html(s)))

    def test_sneaky_import_in_style(self):
        # Prevent "@@importimport" -> "@import" replacement etc.
        style_codes = [
            "@@importimport(extstyle.css)",
            "@ @  import import(extstyle.css)",
            "@ @ importimport(extstyle.css)",
            "@@  import import(extstyle.css)",
            "@ @import import(extstyle.css)",
            "@@importimport()",
            "@@importimport()  ()",
            "@/* ... */import()",
            "@im/* ... */port()",
            "@ @import/* ... */import()",
            "@    /* ... */      import()",
        ]
        for style_code in style_codes:
            html = '<style>%s</style>' % style_code
            s = lxml.html.fragment_fromstring(html)

            cleaned = lxml.html.tostring(clean_html(s))
            self.assertEqual(
                b'<style>/* deleted */</style>',
                cleaned,
                "%s  ->  %s" % (style_code, cleaned))

    def test_sneaky_schemes_in_style(self):
        style_codes = [
            "javasjavascript:cript:",
            "javascriptjavascript::",
            "javascriptjavascript:: :",
            "vbjavascript:cript:",
        ]
        for style_code in style_codes:
            html = '<style>%s</style>' % style_code
            s = lxml.html.fragment_fromstring(html)

            cleaned = lxml.html.tostring(clean_html(s))
            self.assertEqual(
                b'<style>/* deleted */</style>',
                cleaned,
                "%s  ->  %s" % (style_code, cleaned))

    def test_sneaky_urls_in_style(self):
        style_codes = [
            "url(data:image/svg+xml;base64,...)",
            "url(javasjavascript:cript:)",
            "url(javasjavascript:cript: ::)",
            "url(vbjavascript:cript:)",
            "url(vbjavascript:cript: :)",
        ]
        for style_code in style_codes:
            html = '<style>%s</style>' % style_code
            s = lxml.html.fragment_fromstring(html)

            cleaned = lxml.html.tostring(clean_html(s))
            self.assertEqual(
                b'<style>url()</style>',
                cleaned,
                "%s  ->  %s" % (style_code, cleaned))

    def test_svg_data_links(self):
        # Remove SVG images with potentially insecure content.
        svg = b'<svg onload="alert(123)" />'
        gzout = io.BytesIO()
        f = gzip.GzipFile(fileobj=gzout, mode='wb')
        f.write(svg)
        f.close()
        svgz = gzout.getvalue()
        svg_b64 = base64.b64encode(svg).decode('ASCII')
        svgz_b64 = base64.b64encode(svgz).decode('ASCII')
        urls = [
            "data:image/svg+xml;base64," + svg_b64,
            "data:image/svg+xml-compressed;base64," + svgz_b64,
        ]
        for url in urls:
            html = '<img src="%s">' % url
            s = lxml.html.fragment_fromstring(html)

            cleaned = lxml.html.tostring(clean_html(s))
            self.assertEqual(
                b'<img src="">',
                cleaned,
                "%s  ->  %s" % (url, cleaned))

    def test_image_data_links(self):
        data = b'123'
        data_b64 = base64.b64encode(data).decode('ASCII')
        urls = [
            "data:image/jpeg;base64," + data_b64,
            "data:image/apng;base64," + data_b64,
            "data:image/png;base64," + data_b64,
            "data:image/gif;base64," + data_b64,
            "data:image/webp;base64," + data_b64,
            "data:image/bmp;base64," + data_b64,
            "data:image/tiff;base64," + data_b64,
            "data:image/x-icon;base64," + data_b64,
        ]
        for url in urls:
            html = '<img src="%s">' % url
            s = lxml.html.fragment_fromstring(html)

            cleaned = lxml.html.tostring(clean_html(s))
            self.assertEqual(
                html.encode("UTF-8"),
                cleaned,
                "%s  ->  %s" % (url, cleaned))

    def test_image_data_links_in_style(self):
        data = b'123'
        data_b64 = base64.b64encode(data).decode('ASCII')
        urls = [
            "data:image/jpeg;base64," + data_b64,
            "data:image/apng;base64," + data_b64,
            "data:image/png;base64," + data_b64,
            "data:image/gif;base64," + data_b64,
            "data:image/webp;base64," + data_b64,
            "data:image/bmp;base64," + data_b64,
            "data:image/tiff;base64," + data_b64,
            "data:image/x-icon;base64," + data_b64,
        ]
        for url in urls:
            html = '<style> url(%s) </style>' % url
            s = lxml.html.fragment_fromstring(html)

            cleaned = lxml.html.tostring(clean_html(s))
            self.assertEqual(
                html.encode("UTF-8"),
                cleaned,
                "%s  ->  %s" % (url, cleaned))

    def test_image_data_links_in_inline_style(self):
        safe_attrs = set(lxml.html.defs.safe_attrs)
        safe_attrs.add('style')

        cleaner = Cleaner(
            safe_attrs_only=True,
            safe_attrs=safe_attrs)

        data = b'123'
        data_b64 = base64.b64encode(data).decode('ASCII')
        url = "url(data:image/jpeg;base64,%s)" % data_b64
        styles = [
            "background: %s" % url,
            "background: %s; background-image: %s" % (url, url),
        ]
        for style in styles:
            html = '<div style="%s"></div>' % style
            s = lxml.html.fragment_fromstring(html)

            cleaned = lxml.html.tostring(cleaner.clean_html(s))
            self.assertEqual(
                html.encode("UTF-8"),
                cleaned,
                "%s  ->  %s" % (style, cleaned))

    def test_formaction_attribute_in_button_input(self):
        # The formaction attribute overrides the form's action and should be
        # treated as a malicious link attribute
        html = ('<form id="test"><input type="submit" formaction="javascript:alert(1)"></form>'
        '<button form="test" formaction="javascript:alert(1)">X</button>')
        expected = ('<div><form id="test"><input type="submit" formaction=""></form>'
        '<button form="test" formaction="">X</button></div>')
        cleaner = Cleaner(
            forms=False,
            safe_attrs_only=False,
        )
        self.assertEqual(
            expected,
            cleaner.clean_html(html))

    def test_host_whitelist_slash_type_confusion(self):
        # Regression test: Accidentally passing a string when a 1-tuple was intended
        # creates a host_whitelist of the empty string; a malformed triple-slash
        # URL has an "empty host" according to urlsplit, and `"" in ""` passes.
        # So, don't allow user to accidentally pass a string for host_whitelist.
        html = '<div><iframe src="https:///evil.com/page"></div>'
        with self.assertRaises(TypeError) as exc:
            # If this were the intended `("example.com",)` the expected
            # output would be '<div></div>'
            Cleaner(frames=False, host_whitelist=("example.com")).clean_html(html)

        self.assertEqual(("Expected a collection, got str: host_whitelist='example.com'",), exc.exception.args)

    def test_host_whitelist_valid(self):
        # Frame with valid hostname in src is allowed.
        html = '<div><iframe src="https://example.com/page"></iframe></div>'
        expected = '<div><iframe src="https://example.com/page"></iframe></div>'
        cleaner = Cleaner(frames=False, host_whitelist=["example.com"])
        self.assertEqual(expected, cleaner.clean_html(html))

    def test_host_whitelist_invalid(self):
        html = '<div><iframe src="https://evil.com/page"></iframe></div>'
        expected = '<div></div>'
        cleaner = Cleaner(frames=False, host_whitelist=["example.com"])
        self.assertEqual(expected, cleaner.clean_html(html))

    def test_host_whitelist_sneaky_userinfo(self):
        # Regression test: Don't be fooled by hostname and colon in userinfo.
        html = '<div><iframe src="https://example.com:@evil.com/page"></iframe></div>'
        expected = '<div></div>'
        cleaner = Cleaner(frames=False, host_whitelist=["example.com"])
        self.assertEqual(expected, cleaner.clean_html(html))

    def test_ascii_control_chars_removed(self):
        html = """<a href="java\x1bscript:alert()">Link</a>"""
        expected = """<a href="">Link</a>"""
        cleaner = Cleaner()
        self.assertEqual(expected, cleaner.clean_html(html))

    def test_ascii_control_chars_removed_from_bytes(self):
        html = b"""<a href="java\x1bscript:alert()">Link</a>"""
        expected = b"""<a href="">Link</a>"""
        cleaner = Cleaner()
        self.assertEqual(expected, cleaner.clean_html(html))

    def test_memory_usage_many_elements_with_long_tails(self):
        comment = "<!-- foo bar baz -->\n"
        empty_line = "\t" * 10 + "\n"
        element = comment + empty_line * 10
        content = element * 5_000
        html = f"<html>{content}</html>"

        cleaner = Cleaner()
        mem = peak_memory_usage(cleaner.clean_html, html)

        self.assertTrue(mem < 10, f"Used {mem} MiB memory, expected at most 10 MiB")

    def test_possibly_invalid_url_with_whitelist(self):
        cleaner = Cleaner(host_whitelist=['google.com'])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = cleaner.clean_html(r"<p><iframe src='http://example.com:\@google.com'>  </iframe></p>")
            self.assertGreaterEqual(len(w), 1)
            self.assertIs(w[-1].category, AmbiguousURLWarning)
            self.assertTrue(issubclass(w[-1].category, LXMLHTMLCleanWarning))
            self.assertIn("impossible to parse the hostname", str(w[-1].message))
        self.assertNotIn("google.com", result)
        self.assertNotIn("example.com", result)

    def test_possibly_invalid_url_without_whitelist(self):
        cleaner = Cleaner()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = cleaner.clean_html(r"<p><iframe src='http://example.com:\@google.com'>  </iframe></p>")
            self.assertEqual(len(w), 0)
        self.assertNotIn("google.com", result)
        self.assertNotIn("example.com", result)

    def test_base_tag_removed_with_page_structure(self):
        # Test that <base> tags are removed when page_structure=True (default)
        # This prevents URL hijacking attacks where <base> redirects all relative URLs

        test_cases = [
            # <base> in proper location (inside <head>)
            '<html><head><base href="http://evil.com/"></head><body><a href="page.html">link</a></body></html>',
            # <base> outside <head>
            '<div><base href="http://evil.com/"><a href="page.html">link</a></div>',
            # Multiple <base> tags
            '<base href="http://evil.com/"><div><base href="http://evil2.com/"></div>',
            # <base> with target attribute
            '<base target="_blank"><div>content</div>',
            # <base> at various positions
            '<html><base href="http://evil.com/"><body>test</body></html>',
        ]

        for html in test_cases:
            with self.subTest(html=html):
                cleaned = clean_html(html)
                # Verify <base> tag is completely removed
                self.assertNotIn('base', cleaned.lower())
                self.assertNotIn('evil.com', cleaned)
                self.assertNotIn('evil2.com', cleaned)

    def test_base_tag_kept_when_page_structure_false(self):
        # When page_structure=False and head is not removed, <base> should be kept
        cleaner = Cleaner(page_structure=False)
        html = '<html><head><base href="http://example.com/"></head><body>test</body></html>'
        cleaned = cleaner.clean_html(html)
        self.assertIn('<base href="http://example.com/">', cleaned)

    def test_base_tag_removed_when_head_in_remove_tags(self):
        # Even with page_structure=False, <base> should be removed if head is manually removed
        cleaner = Cleaner(page_structure=False, remove_tags=['head'])
        html = '<html><head><base href="http://evil.com/"></head><body>test</body></html>'
        cleaned = cleaner.clean_html(html)
        self.assertNotIn('base', cleaned.lower())
        self.assertNotIn('evil.com', cleaned)

    def test_base_tag_removed_when_head_in_kill_tags(self):
        # Even with page_structure=False, <base> should be removed if head is in kill_tags
        cleaner = Cleaner(page_structure=False, kill_tags=['head'])
        html = '<html><head><base href="http://evil.com/"></head><body>test</body></html>'
        cleaned = cleaner.clean_html(html)
        self.assertNotIn('base', cleaned.lower())
        self.assertNotIn('evil.com', cleaned)

    def test_unicode_escape_in_style(self):
        # Test that CSS Unicode escapes are properly decoded before security checks
        # This prevents attackers from bypassing filters using escape sequences
        # CSS escape syntax: \HHHHHH where H is a hex digit (1-6 digits)

        # Test inline style attributes (requires safe_attrs_only=False)
        cleaner = Cleaner(safe_attrs_only=False)
        inline_style_cases = [
            # \6a\61\76\61\73\63\72\69\70\74 = "javascript"
            ('<div style="background: url(\\6a\\61\\76\\61\\73\\63\\72\\69\\70\\74:alert(1))">test</div>', '<div>test</div>'),
            # \69 = 'i', so \69mport = "import"
            ('<div style="@\\69mport url(evil.css)">test</div>', '<div>test</div>'),
            # \69 with space after = 'i', space consumed as part of escape
            ('<div style="@\\69 mport url(evil.css)">test</div>', '<div>test</div>'),
            # \65\78\70\72\65\73\73\69\6f\6e = "expression"
            ('<div style="\\65\\78\\70\\72\\65\\73\\73\\69\\6f\\6e(alert(1))">test</div>', '<div>test</div>'),
        ]

        for html, expected in inline_style_cases:
            with self.subTest(html=html):
                cleaned = cleaner.clean_html(html)
                self.assertEqual(expected, cleaned)

        # Test <style> tag content (uses default clean_html)
        style_tag_cases = [
            # Unicode-escaped "javascript:" in url()
            '<style>url(\\6a\\61\\76\\61\\73\\63\\72\\69\\70\\74:alert(1))</style>',
            # Unicode-escaped "javascript:" without url()
            '<style>\\6a\\61\\76\\61\\73\\63\\72\\69\\70\\74:alert(1)</style>',
            # Unicode-escaped "expression"
            '<style>\\65\\78\\70\\72\\65\\73\\73\\69\\6f\\6e(alert(1))</style>',
            # Unicode-escaped @import with 'i'
            '<style>@\\69mport url(evil.css)</style>',
            # Unicode-escaped "data:" scheme
            '<style>url(\\64\\61\\74\\61:image/svg+xml;base64,PHN2ZyBvbmxvYWQ9YWxlcnQoMSk+)</style>',
            # Space after escape is consumed: \69 mport = "import"
            '<style>@\\69 mport url(evil.css)</style>',
            # 6-digit escape: \000069 = 'i'
            '<style>@\\000069mport url(evil.css)</style>',
            # 6-digit escape with space
            '<style>@\\000069 mport url(evil.css)</style>',
        ]

        for html in style_tag_cases:
            with self.subTest(html=html):
                cleaned = clean_html(html)
                self.assertEqual('<div><style>/* deleted */</style></div>', cleaned)

    def test_unicode_escape_mixed_with_comments(self):
        # Unicode escapes mixed with CSS comments should still be caught
        test_cases = [
            # \69 = 'i' with comment before
            '<style>@/*comment*/\\69mport url(evil.css)</style>',
            # \69 = 'i' with comment after
            '<style>@\\69mport/*comment*/ url(evil.css)</style>',
            # Multiple escapes with comments
            '<style>\\65\\78/*comment*/\\70\\72\\65\\73\\73\\69\\6f\\6e(alert(1))</style>',
        ]

        for html in test_cases:
            with self.subTest(html=html):
                cleaned = clean_html(html)
                self.assertEqual('<div><style>/* deleted */</style></div>', cleaned)

    def test_unicode_escape_case_insensitive(self):
        # CSS hex escapes should work with both uppercase and lowercase hex digits
        # \69 = 'i', \6D = 'm', etc.
        test_cases = [
            # @import with uppercase hex digits: \69\6D\70\6F\72\74
            '<style>@\\69\\6D\\70\\6F\\72\\74 url(evil.css)</style>',
            # @import with some uppercase
            '<style>@\\69\\6D\\70\\6f\\72\\74 url(evil.css)</style>',
        ]

        for html in test_cases:
            with self.subTest(html=html):
                cleaned = clean_html(html)
                self.assertEqual('<div><style>/* deleted */</style></div>', cleaned)

    def test_unicode_escape_various_schemes(self):
        # Test Unicode escapes for various malicious schemes
        test_cases = [
            # \76\62\73\63\72\69\70\74 = "vbscript"
            '<style>url(\\76\\62\\73\\63\\72\\69\\70\\74:alert(1))</style>',
            # \6a\73\63\72\69\70\74 = "jscript"
            '<style>url(\\6a\\73\\63\\72\\69\\70\\74:alert(1))</style>',
            # \6c\69\76\65\73\63\72\69\70\74 = "livescript"
            '<style>url(\\6c\\69\\76\\65\\73\\63\\72\\69\\70\\74:alert(1))</style>',
            # \6d\6f\63\68\61 = "mocha"
            '<style>url(\\6d\\6f\\63\\68\\61:alert(1))</style>',
        ]

        for html in test_cases:
            with self.subTest(html=html):
                cleaned = clean_html(html)
                self.assertEqual('<div><style>/* deleted */</style></div>', cleaned)

    def test_unicode_escape_with_whitespace_variations(self):
        # Test different whitespace characters after Unicode escapes
        cleaner = Cleaner(safe_attrs_only=False)
        test_cases = [
            # Tab after escape
            ('<div style="@\\69\tmport url(evil.css)">test</div>', '<div>test</div>'),
            # Newline after escape (note: actual newline, not \n)
            ('<div style="@\\69\nmport url(evil.css)">test</div>', '<div>test</div>'),
            # Form feed after escape
            ('<div style="@\\69\fmport url(evil.css)">test</div>', '<div>test</div>'),
        ]

        for html, expected in test_cases:
            with self.subTest(html=html):
                cleaned = cleaner.clean_html(html)
                self.assertEqual(expected, cleaned)

    def test_backslash_removal_after_unicode_decode(self):
        # After decoding Unicode escapes, remaining backslashes are removed
        # This ensures double-obfuscation (unicode + backslashes) is caught
        test_cases = [
            # Step 1: \69 → 'i', Step 2: remove \, Result: @import
            '<style>@\\69\\m\\p\\o\\r\\t url(evil.css)</style>',
            # Multiple unicode escapes with backslashes mixed in
            '<style>@\\69\\6d\\p\\6f\\r\\t url(evil.css)</style>',
        ]

        for html in test_cases:
            with self.subTest(html=html):
                cleaned = clean_html(html)
                self.assertEqual('<div><style>/* deleted */</style></div>', cleaned)

    def test_backslash_obfuscation_without_unicode(self):
        # Test that patterns using ONLY backslash obfuscation (no unicode) are caught
        # Step 1: No unicode escapes, Step 2: remove \, Result: malicious pattern
        test_cases = [
            # @\i\m\p\o\r\t → @import (caught by '@import' check)
            '<style>@\\i\\m\\p\\o\\r\\t url(evil.css)</style>',
            # Can also test combinations that create javascript schemes
            '<style>@\\import url(evil.css)</style>',
        ]

        for html in test_cases:
            with self.subTest(html=html):
                cleaned = clean_html(html)
                self.assertEqual('<div><style>/* deleted */</style></div>', cleaned)
