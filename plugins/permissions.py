from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Union, cast

from sqlalchemy import and_, delete, literal, select, union
from sqlalchemy.sql import Select

import databases.database as d
from database import Database
from plugins import Command, command_wrapper, htmlpage_wrapper
from typedefs import Role

if TYPE_CHECKING:
    from models.message import Message
    from models.room import Room
    from models.user import User


@command_wrapper(required_rank="owner", parametrize_room=True)
async def setpermission(msg: Message) -> None:
    room = msg.parametrized_room

    if len(msg.args) != 3:
        return

    command = msg.args[0]
    if command not in Command.get_rank_editable_commands():
        return

    rank = msg.args[2]
    if rank not in (
        "default",
        "regularuser",
        "voice",
        "driver",
        "mod",
        "owner",
        "admin",
        "disabled",
    ):
        return
    rank = cast(Union[Role, Literal["default"]], rank)

    db = Database.open()
    with db.get_session() as session:
        if rank == "default":
            stmt = delete(d.CustomPermissions).filter_by(
                roomid=room.roomid, command=command
            )
            session.execute(stmt)
        else:
            session.add(
                d.CustomPermissions(
                    roomid=room.roomid, command=command, required_rank=rank
                )
            )

    await room.send_modnote(
        "PERMISSIONS", msg.user, f"set the required rank for {command} to {rank}"
    )

    try:
        page = int(msg.args[1])
    except ValueError:
        page = 1

    await msg.user.send_htmlpage("permissions", room, page, scroll_to_top=False)


@htmlpage_wrapper("permissions", aliases=("permission",), required_rank="owner")
def permissions_htmlpage(user: User, room: Room) -> Select:
    stmts = (
        select(literal(i).label("command_name"))
        for i in Command.get_rank_editable_commands()
    )
    commands = union(*stmts).alias("commands")

    # TODO: remove annotation
    stmt: Select = (
        select(commands.c.command_name, d.CustomPermissions)
        .select_from(commands)
        .outerjoin(
            d.CustomPermissions,
            and_(
                d.CustomPermissions.roomid == room.roomid,
                commands.c.command_name == d.CustomPermissions.command,
            ),
        )
        .order_by(commands.c.command_name)
    )
    return stmt
