from __future__ import annotations

from typing import TYPE_CHECKING

from cerbottana.html_utils import BaseHTMLCommand

from . import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


class ColorCompareHTML(BaseHTMLCommand):
    _STYLES = {
        "table": {
            "table-layout": "fixed",
            "width": "100%",
        },
        "background1": {
            "box-shadow": "inset 0 0 0 100vh, 0 30px",
            "height": "30px",
        },
        "username": {
            "font-weight": "bold",
            "text-align": "center",
        },
        "background2": {
            "box-shadow": "inset 0 0 0 100vh, 0 -30px",
            "height": "30px",
        },
    }

    def __init__(self, *, usernames: list[str]) -> None:
        super().__init__()

        tag = self.doc.tag
        line = self.doc.line

        with tag("table", style=self._get_css("table")), tag("tr"):

            for username in usernames:
                with tag("td"):

                    with tag("username", name=username):
                        line("div", "", style=self._get_css("background1"))

                    line("div", username, style=self._get_css("username"))

                    with tag("username", name=username):
                        line("div", "", style=self._get_css("background2"))


@command_wrapper(
    aliases=("cc",),
    helpstr="<i>nick1, nick2, ...</i> Visualizza i colori dei nickname elencati.",
    required_rank_editable=True,
)
async def colorcompare(msg: Message) -> None:
    # Ignore empty args: they're usually typos, i.e. "a,,b".
    args = [arg for arg in msg.args if arg]
    if not args:
        return

    html = ColorCompareHTML(usernames=args)
    await msg.reply_htmlbox(html.doc)
