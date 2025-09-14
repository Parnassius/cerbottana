from __future__ import annotations

import math
import random
import re
import string
from collections.abc import Callable, Mapping
from html import escape
from typing import TYPE_CHECKING

from domify import html_elements as e
from domify.base_element import BaseElement
from imageprobe import probe
from sqlalchemy import func
from sqlalchemy.engine import Row
from sqlalchemy.sql import Select

from cerbottana.database import Database

if TYPE_CHECKING:
    import aiohttp

    from cerbottana.models.room import Room
    from cerbottana.models.user import User


async def image_url_to_html(url: str, *, session: aiohttp.ClientSession) -> BaseElement:
    """Generates an <img> tag from an image url."""
    image = await probe(url, session=session)
    return e.Img(src=url, width=image.width, height=image.height)


def linkify(text: str) -> str:
    """Transforms a text containing URLs into HTML code.

    Args:
        text (str): Raw text.

    Returns:
        str: Escaped HTML, possibly containing <a> tags.
    """
    # Partially translated from https://github.com/smogon/pokemon-showdown, chat parser.
    # The original code is released under the MIT License.

    # linkify requires a custom translation table because "/" is left unescaped.
    table = {ord(char): escape(char) for char in "&<>\"'"}
    table[ord("\n")] = "<br>"
    text = text.translate(table)

    url_regex = r'(?i)(?:(?:https?:\/\/[a-z0-9-]+(?:\.[a-z0-9-]+)*|www\.[a-z0-9-]+(?:\.[a-z0-9-]+)+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com?|org|net|edu|info|us|jp|[a-z]{2,3}(?=[:/])))(?::[0-9]+)?(?:\/(?:(?:[^\s()&<>]|&amp;|&quot;|\((?:[^\\s()<>&]|&amp;)*\))*(?:[^\s()[\]{}".,!?;:&<>*`^~\\]|\((?:[^\s()<>&]|&amp;)*\)))?)?|[a-z0-9.]+@[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,})(?![^ ]*&gt;)'  # noqa: E501
    return re.sub(url_regex, lambda m: _linkify_uri(m.group()), text)


def _linkify_uri(uri: str) -> str:
    # Partially translated from https://github.com/smogon/pokemon-showdown, chat parser.
    # The original code is released under the MIT License.

    if re.match(r"^[a-z0-9.]+@", uri, re.IGNORECASE):
        fulluri = f"mailto:{uri}"
    else:
        fulluri = re.sub(r"^([a-z]*[^a-z:])", r"http://\1", uri)
        if uri.startswith(("https://docs.google.com/", "docs.google.com/")):
            if uri.startswith("https"):
                uri = uri[8:]
            if uri.endswith(("?usp=sharing", "&usp=sharing")):
                uri = uri[:-12]
            if uri.endswith("#gid=0"):
                uri = uri[:-6]

            slash_index = uri.rindex("/")
            if len(uri) - slash_index > 18:
                slash_index = len(uri)
            if slash_index - 4 > 22:
                uri = (
                    uri[:19]
                    + '<small class="message-overflow">'
                    + uri[19 : slash_index - 4]
                    + "</small>"
                    + uri[slash_index - 4 :]
                )
    return f'<a href="{fulluri}">{uri}</a>'


def to_obfuscated_html(text: str) -> BaseElement:
    """Converts a string to HTML code and adds invisible obfuscation text."""
    html = BaseElement()
    for ch in text:
        randstr = ""
        for _ in range(random.randrange(3, 10)):
            randstr += random.choice(string.ascii_letters + string.digits)
        html.add(ch + e.Span(randstr, style="position: absolute; top: -999vh"))
    return html


class BaseHTMLCommand:
    """Base class to implement html commands and html pages"""

    _STYLES: Mapping[str, Mapping[str, str]] = {}

    def __init__(self) -> None:
        self.doc = e.BaseElement()

    def __bool__(self) -> bool:
        return bool(len(self.doc))

    def _get_css(self, element: str) -> str:
        return ";".join([f"{k}:{v}" for k, v in self._STYLES.get(element, {}).items()])


class HTMLPageCommand(BaseHTMLCommand):
    _STYLES = {  # noqa: RUF012
        "btn_disabled": {
            "background": "#D3D3D3",
            "color": "#575757",
            "font-weight": "bold",
        },
        "one_pixel_width": {
            "white-space": "nowrap",
            "width": "1px",
        },
    }

    def __init__(
        self,
        user: User,
        room: Room,
        command: str,
        stmt: Select,  # type: ignore[type-arg]
        *,
        title: str,
        fields: list[  # type: ignore[type-arg]
            tuple[str, str | Callable[[Row], BaseElement | str]]
        ],
        actions_header: str = "",
        actions: (  # type: ignore[type-arg]
            list[
                tuple[
                    str,  # cmd
                    list[str | Callable[[Row], str]],  # params
                    bool | Callable[[Row], bool],  # disabled
                    str | None,  # btn_icon
                    str,  # btn_text
                ]
            ]
            | None
        ) = None,
    ) -> None:
        super().__init__()

        self._user = user
        self._room = room
        self._botname = room.conn.username
        self._cmd_char = room.conn.command_character
        self._commands = room.conn.commands
        self._command = command
        self._page = 1
        self._title = title
        self._stmt = stmt
        self._fields = fields
        self._actions_header = actions_header
        self._actions = actions or []

    def load_page(self, page: int) -> None:
        db = Database.open()
        with db.get_session() as session:
            stmt_last_page = self._stmt.with_only_columns(func.count())
            last_page = math.ceil(session.scalars(stmt_last_page).one() / 100)
            page = min(page, last_page)
            stmt_rs = self._stmt.limit(100).offset(100 * (page - 1))

            rs = session.execute(stmt_rs).all()

            with self.doc, e.Div(class_="pad"):
                e.H2(self._title)
                if not rs:
                    e.TextNode("No results found")
                    return

                with e.Div(class_="ladder"), e.Table():
                    with e.Tr():
                        for field_header, _ in self._fields:
                            e.Th(field_header)
                        e.Th(self._actions_header)

                    for row in rs:
                        with e.Tr():
                            for _, field in self._fields:
                                e.Td(
                                    str(getattr(row[0], field) or "")
                                    if isinstance(field, str)
                                    else field(row)
                                )

                            with e.Td(style=self._get_css("one_pixel_width")):
                                self._add_action_buttons(row)

                page_cmd = (
                    f"/pm {self._botname}, {self._cmd_char}changepage "
                    f"{self._command}, {self._room.roomid}, "
                )
                for p in range(last_page):
                    with e.Button(p + 1, class_="option") as btn:
                        if page == p + 1:
                            btn.add_class("sel")
                            btn["disabled"] = True
                        else:
                            btn["name"] = "send"
                            btn["value"] = f"{page_cmd}{p + 1}"

    def _add_action_buttons(self, row: Row) -> None:  # type: ignore[type-arg]
        for cmd, params, disabled, btn_icon, btn_text in self._actions:
            req_rank = self._commands[cmd].get_required_rank(self._room.roomid, False)
            if not self._user.has_role(req_rank, self._room):
                continue

            cmd_params = []
            for param in params:
                if isinstance(param, str):
                    if param.startswith("__"):
                        cmd_params.append(param[2:])
                    elif param == "_roomid":
                        cmd_params.append(self._room.roomid)
                    elif param == "_page":
                        cmd_params.append(str(self._page))
                    else:
                        cmd_params.append(str(getattr(row[0], param) or ""))
                else:
                    cmd_params.append(param(row))
            cmd = f"/pm {self._botname}, {self._cmd_char}{cmd} " + ",".join(cmd_params)

            with e.Button(f" {btn_text}", class_="button") as btn:
                if not isinstance(disabled, bool):
                    disabled = disabled(row)
                if disabled:
                    btn.add_class("disabled")
                    btn["style"] = self._get_css("btn_disabled")
                else:
                    btn["name"] = "send"
                    btn["value"] = cmd
                if btn_icon:
                    btn.insert(0, e.I(class_=f"fa fa-{btn_icon}"))
            e.TextNode(" ")
