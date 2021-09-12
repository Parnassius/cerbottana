from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update

import databases.database as d
from database import Database
from plugins import command_wrapper
from utils import get_ps_dex_entry, to_id

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("icons", "userlisticon", "userlisticons"))
async def icon(msg: Message) -> None:
    if len(msg.args) < 1:
        await msg.reply(
            "You can set your Pokémon using "
            f"``{msg.conn.command_character}icon <pokemon>``, "
            "or install the userstyle (https://git.io/JuoFg) "
            "using Stylus (https://add0n.com/stylus.html)."
        )
        return

    search_query = to_id(msg.args[0])
    dex_entry = get_ps_dex_entry(search_query)
    if dex_entry is None or dex_entry["num"] < 0:
        await msg.reply("Pokémon not found.")
        return

    db = Database.open()
    with db.get_session() as session:
        userid = msg.user.userid
        session.add(d.Users(userid=userid))
        stmt = (
            update(d.Users)
            .filter_by(userid=userid)
            .values(icon=to_id(dex_entry["dex_name"]))
        )
        session.execute(stmt)

        # Update the CSV file
        stmt_csv = (
            select(d.Users.userid, d.Users.icon)
            .where(d.Users.icon.is_not(None))
            .order_by(d.Users.userid)
        )
        with open("./userlist_icons.csv", "w", encoding="utf-8") as f:
            f.writelines(
                [f"{userid},{icon}\n" for userid, icon in session.execute(stmt_csv)]
            )

    await msg.reply(
        "Done. Your Pokémon might take up to 24 hours to appear on the userstyle."
    )
