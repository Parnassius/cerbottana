from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, Union, cast

from domify.base_element import BaseElement
from sqlalchemy import and_, delete, literal, select, union
from sqlalchemy.engine import Row
from sqlalchemy.sql import Select

import cerbottana.databases.database as d
from cerbottana.database import Database
from cerbottana.html_utils import HTMLPageCommand
from cerbottana.typedefs import Role

from . import Command, command_wrapper, htmlpage_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message
    from cerbottana.models.room import Room
    from cerbottana.models.user import User


PERMISSION_ROLES = {
    "default": "default",
    "regularuser": "regular",
    "voice": "+",
    "driver": "%",
    "mod": "@",
    "owner": "#",
    "admin": "&",
    "disabled": "disabled",
}


@command_wrapper(required_rank="owner", parametrize_room=True)
async def setpermission(msg: Message) -> None:
    room = msg.parametrized_room

    if len(msg.args) != 3:
        return

    command = msg.args[0]
    if command not in Command.get_rank_editable_commands():
        return

    rank = msg.args[2]
    if rank not in PERMISSION_ROLES.keys():
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
def permissions_htmlpage(user: User, room: Room, page: int) -> BaseElement:
    stmts = (
        select(literal(i).label("command_name"))
        for i in Command.get_rank_editable_commands()
    )
    commands = union(*stmts).alias("commands")

    # TODO: remove annotation
    stmt: Select = (
        select(d.CustomPermissions, commands.c.command_name)
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

    def btn_disabled(role: str) -> Callable[[Row], bool]:
        if role == "default":
            return lambda row: row.CustomPermissions is None
        return lambda row: (
            row.CustomPermissions is not None
            and row.CustomPermissions.required_rank == role
        )

    html = HTMLPageCommand(
        user,
        room,
        "permissions",
        stmt,
        title=f"Command permissions for {room.title}",
        fields=[("Permission", lambda row: str(row.command_name))],
        actions_header="Required rank",
        actions=[
            (
                "setpermission",
                [
                    "_roomid",
                    lambda row: row.command_name,  # type: ignore[no-any-return]
                    "_page",
                    f"__{role}",
                ],
                btn_disabled(role),
                None,
                role_symbol,
            )
            for role, role_symbol in PERMISSION_ROLES.items()
        ],
    )

    html.load_page(page)

    return html.doc
