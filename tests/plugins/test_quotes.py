from __future__ import annotations

import pytest

from cerbottana.plugins.quotes import to_html_quotebox


@pytest.mark.parametrize(
    ("testquote", "n_parsed_lines"),
    [
        # (testquote, nr. of parsed lines in the resulting quotebox),
        #
        # Only chat messages
        ("[21:33] @plat0: test a one-liner [this:is] not another timestamp", 1),
        ("[21:33:34] @plat0: test a one-liner [this:is:not] another timestamp", 1),
        ("[21:33] @plato:", 1),
        ("[21:33] @plat0: test1 [21:33] @plat0: test2 [21:33] +Ihmsan: test3", 3),
        ("[21:33:20] @plat0: t1 [21:33:21] @plat0: t2 [21:33:22] +Ihmsan: t3", 3),
        # Chat messages + single-line PS messages)
        ("[19:22] • %plat0 metest [19:22] %plat0: test [19:23] +Ihmsan: Hi!", 3),
        ("[19:36] A was unmuted by B. [19:37] %B: ! [19:37] A was muted by B for..", 3),
        # Chat messages + multi-line PS messages)
        ("[13:51] (plat0 created a tour.) [Gen 7] Tour created. [13:52] %plat0: Oh", 3),
        # Unparsed quotes ~ 1 unparsed line (0 parsed lines)
        ("normal quote", 0),
        ("[21:33]", 0),
        ("[21:33:34]", 0),
        ("[21:33][21:34]", 0),
        ("[21:33] [21:34]", 0),
        ("[21:33 @plat0: test a one-liner with a missing right bracket", 0),
        ("salt [21:33] @plat0: test1 [21:33] @plat0: test2 [21:33] +Ihmsan: test3", 0),
        ("(There is a parentheses regex too, you never know!)", 0),
    ],
)
def test_to_html_quotebox_chat(testquote: str, n_parsed_lines: int) -> None:
    """Tests that chatlines are splitted correctly (or left unparsed)."""
    quotebox = to_html_quotebox(testquote)
    assert quotebox.count('<div class="chat">') == n_parsed_lines


@pytest.mark.parametrize(
    ("chatline", "is_colorized"),
    [
        # Single-line quotes.
        ("[21:33] reg: testline", True),
        ("[21:33] @auth: testline", True),
        ("[21:33] reg: hey: +how: are: @you", True),
        ("reg: auth", False),
        ("[21:33] (Plato notes: reason)", False),
    ],
)
def test_to_html_quotebox_colorize(chatline: str, is_colorized: bool) -> None:
    """Tests that usernames are colorized only once per line and if necessary."""
    quotebox = to_html_quotebox(chatline)
    tag_count = int(is_colorized)  # Occurrences of <username>, at most 1.
    assert quotebox.count("<username>") == tag_count


def test_to_html_quotebox_empty() -> None:
    """Tests that empty quotes raise an exception."""
    with pytest.raises(
        ValueError, match=r"^Trying to create quotebox for empty quote\.$"
    ):
        to_html_quotebox("")
