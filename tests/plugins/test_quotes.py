from __future__ import annotations

import pytest

import plugins.quotes as quotes


@pytest.mark.parametrize(
    "testquote, n_parsed_lines",
    (
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
    ),
)
def test_to_html_quotebox_chat(testquote: str, n_parsed_lines: int) -> None:
    quotebox = quotes.to_html_quotebox(testquote)
    assert quotebox.count('<div class="chat">') == n_parsed_lines


def test_to_html_quotebox_empty() -> None:
    with pytest.raises(BaseException):
        quotes.to_html_quotebox("")
