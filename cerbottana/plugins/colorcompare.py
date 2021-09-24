from __future__ import annotations

from typing import TYPE_CHECKING

from domify import html_elements as e

from cerbottana import custom_elements as ce
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

        with self.doc, e.Table(style=self._get_css("table")), e.Tr():

            for username in usernames:
                with e.Td():

                    with ce.Username(name=username):
                        e.Div(style=self._get_css("background1"))

                    e.Div(username, style=self._get_css("username"))

                    with ce.Username(name=username):
                        e.Div(style=self._get_css("background2"))


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
