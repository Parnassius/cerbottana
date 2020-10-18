from __future__ import annotations

from typing import TYPE_CHECKING

from plugins import command_wrapper

if TYPE_CHECKING:
    from models.message import Message


@command_wrapper(aliases=("token",))
async def dashboard(msg: Message) -> None:
    if not msg.conn.main_room or not msg.user.has_role("driver", msg.conn.main_room):
        return

    phrase = (
        "``.dashboard`` è stato rimosso, "
        "per gestire le badge di un utente usa ``.badges <utente>``, "
        "per gestire le risposte di ``.8ball`` usa ``.8ballanswers``, "
        "``.add8ballanswer`` e ``.remove8ballanswer``"
    )
    await msg.user.send(phrase)
