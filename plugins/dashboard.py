from __future__ import annotations

from typing import TYPE_CHECKING

from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("token",), required_rank="driver", main_room_only=True)
async def dashboard(msg: Message) -> None:
    await msg.user.send(
        "``.dashboard`` è stato rimosso, "
        "per gestire le badge di un utente usa ``.badges <utente>``, "
        "per gestire le risposte di ``.8ball`` usa ``.8ballanswers``, "
        "``.add8ballanswer`` e ``.remove8ballanswer``"
    )
