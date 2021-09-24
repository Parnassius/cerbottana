from __future__ import annotations

import pytest

from cerbottana import html_utils


@pytest.mark.parametrize(
    "uri, expected_html",
    [
        # pylint: disable=line-too-long
        ("&  <  >  \"  '", "&amp;  &lt;  &gt;  &quot;  &#x27;"),
        ("a@b.com", '<a href="mailto:a@b.com">a@b.com</a>'),
        ("mailto:a@b.com", 'mailto:<a href="mailto:a@b.com">a@b.com</a>'),
        ("a@b", "a@b"),  # Not a valid email address
        ("gOOgle.com", '<a href="http://gOOgle.com">gOOgle.com</a>'),
        ("https://google.com", '<a href="https://google.com">https://google.com</a>'),
        ("a.bcde", "a.bcde"),  # Not a valid link
        (
            "https://docs.google.com/document/d/1Qw55gu000000WMErXG_empg_BNUbYO3-3qHOau3ezR0/edit?usp=sharing/",
            '<a href="https://docs.google.com/document/d/1Qw55gu000000WMErXG_empg_BNUbYO3-3qHOau3ezR0/edit?usp=sharing/">docs.google.com/doc<small class="message-overflow">ument/d/1Qw55gu000000WMErXG_empg_BNUbYO3-3qHOau3ezR0/edit?usp=sha</small>ring/</a>',
        ),
    ],
)
def test_linkify(uri: str, expected_html: str) -> None:
    assert html_utils.linkify(uri) == expected_html
