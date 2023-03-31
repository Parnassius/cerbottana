from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from domify import html_elements as e
from domify.base_element import BaseElement
from sqlalchemy import select, update

import cerbottana.databases.database as d
from cerbottana import custom_elements as ce
from cerbottana import utils
from cerbottana.database import Database
from cerbottana.html_utils import BaseHTMLCommand, HTMLPageCommand
from cerbottana.plugins import command_wrapper, htmlpage_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message
    from cerbottana.models.room import Room
    from cerbottana.models.user import User


class ProfileHTML(BaseHTMLCommand):
    _STYLES = {
        "avatar": {
            "display": "table-cell",
            "vertical-align": "top",
            "width": "80px",
        },
        "main": {
            "display": "table-cell",
            "vertical-align": "top",
            "width": "100%",
        },
        "badge": {
            "border": "1px solid",
            "border-radius": "2px",
            "margin": "2px 1px 0 0",
        },
        "hr": {
            "margin": "4px 0",
        },
        "description": {
            "text-align": "justify",
        },
        "pokemon_icon": {
            "display": "table-cell",
            "vertical-align": "top",
            "width": "40px",
        },
    }

    def __init__(
        self,
        *,
        avatar_dir: str,
        avatar_name: str,
        username: str,
        badges: Sequence[d.Badges],
        description: str | None,
        pokemon_icon: str | None,
    ) -> None:
        super().__init__()

        with self.doc, e.Div():
            with e.Div(style=self._get_css("avatar")):
                e.Img(
                    src=(
                        "https://play.pokemonshowdown.com/sprites/"
                        f"{avatar_dir}/{avatar_name}.png"
                    ),
                    width=80,
                    height=80,
                )

            with e.Div(style=self._get_css("main")):
                ce.Username(username)
                e.Br()
                for badge in badges:
                    e.Img(
                        src=badge.image,
                        width=13,
                        height=13,
                        title=badge.label,
                        style=self._get_css("badge"),
                    )
                if description:
                    e.Hr(style=self._get_css("hr"))
                    e.Div(description, style=self._get_css("description"))

            if pokemon_icon:
                with e.Div(style=self._get_css("pokemon_icon")):
                    ce.Psicon(pokemon=pokemon_icon)


@command_wrapper(aliases=("profilo",), helpstr="Visualizza il tuo profilo.")
async def profile(msg: Message) -> None:
    userid = utils.to_user_id(msg.arg.strip())
    if userid == "":
        userid = msg.user.userid

    db = Database.open()
    with db.get_session() as session:
        stmt_user = select(d.Users).filter_by(userid=userid)
        userdata = session.scalar(stmt_user)

        if userdata and userdata.userid and userdata.avatar:
            stmt = (
                select(d.Badges).filter_by(userid=userdata.userid).order_by(d.Badges.id)
            )
            badges = session.execute(stmt).scalars().all()

            if userdata.avatar[0] == "#":
                avatar_dir = "trainers-custom"
                avatar_name = userdata.avatar[1:]
            else:
                avatar_dir = "trainers"
                avatar_name = userdata.avatar

            html = ProfileHTML(
                avatar_dir=avatar_dir,
                avatar_name=avatar_name,
                username=userdata.username or userdata.userid,
                badges=badges,
                description=userdata.description,
                pokemon_icon=userdata.icon,
            )

            await msg.reply_htmlbox(html.doc)


@command_wrapper(
    aliases=("setprofilo",), helpstr="Imposta una tua frase personalizzata."
)
async def setprofile(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Specifica una frase da inserire nel tuo profilo")
        return

    if len(msg.arg) > 250:
        await msg.reply("Errore: lunghezza massima 250 caratteri")
        return

    # authorized: True if msg.user can approve new descriptions.
    authorized = msg.user.has_role("driver", msg.conn.main_room)

    db = Database.open()
    with db.get_session() as session:
        userid = msg.user.userid
        session.add(d.Users(userid=userid))
        stmt = update(d.Users).filter_by(userid=userid)
        if authorized:
            # Authorized users skip the validation process.
            stmt = stmt.values(description=msg.arg, description_pending="")
        else:
            stmt = stmt.values(description_pending=msg.arg)
        session.execute(stmt)

    await msg.reply("Salvato")

    if not authorized:
        username = msg.user.username
        botname = msg.conn.username
        cmd = f"{msg.conn.command_character}pendingdescriptions"

        html = f"{username} ha aggiornato la sua frase del profilo." + e.Br()
        html += (
            "Usa "
            + e.Button(cmd, name="send", value=f"/pm {botname}, {cmd}")
            + " per approvarla o rifiutarla"
        )
        await msg.conn.main_room.send_rankhtmlbox("%", html)


@command_wrapper(
    aliases=("clearprofilo", "resetprofile", "resetprofilo"),
    helpstr="Rimuovi la frase personalizzata dal profilo.",
)
async def clearprofile(msg: Message) -> None:
    db = Database.open()
    with db.get_session() as session:
        userid = msg.user.userid
        session.add(d.Users(userid=userid))
        stmt = (
            update(d.Users)
            .filter_by(userid=userid)
            .values(description="", description_pending="")
        )
        session.execute(stmt)

    await msg.reply("Frase rimossa")


@command_wrapper(required_rank="driver", main_room_only=True)
async def approvaprofilo(msg: Message) -> None:
    db = Database.open()

    with db.get_session() as session:
        parts = msg.arg.split(",")
        stmt = (
            update(d.Users)
            .filter_by(id=parts[0], description_pending=",".join(parts[1:]))
            .values(description=d.Users.description_pending, description_pending="")
        )
        session.execute(stmt)

    await msg.user.send_htmlpage("pendingdescriptions", msg.conn.main_room)


@command_wrapper(required_rank="driver", main_room_only=True)
async def rifiutaprofilo(msg: Message) -> None:
    db = Database.open()

    with db.get_session() as session:
        parts = msg.arg.split(",")
        stmt = (
            update(d.Users)
            .filter_by(id=parts[0], description_pending=",".join(parts[1:]))
            .values(description_pending="")
        )
        session.execute(stmt)

    await msg.user.send_htmlpage("pendingdescriptions", msg.conn.main_room)


@htmlpage_wrapper("pendingdescriptions", required_rank="driver", main_room_only=True)
def pendingdescriptions_htmlpage(user: User, room: Room, page: int) -> BaseElement:
    stmt = (
        select(d.Users)
        .where(d.Users.description_pending != "")
        .order_by(d.Users.userid)
    )

    html = HTMLPageCommand(
        user,
        room,
        "pendingdescriptions",
        stmt,
        title="Pending profile descriptions",
        fields=[
            ("User", "username"),
            ("Current description", "description"),
            ("New description", "description_pending"),
        ],
        actions=[
            (
                "approvaprofilo",
                ["id", "description_pending"],
                False,
                "check",
                "Approve",
            ),
            (
                "rifiutaprofilo",
                ["id", "description_pending"],
                False,
                "times",
                "Reject",
            ),
        ],
    )

    html.load_page(page)

    return html.doc
