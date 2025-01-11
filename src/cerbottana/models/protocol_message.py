from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cerbottana.models.room import Room


class ProtocolMessage:
    """Message sent from the Pokemon Showdown server.

    Attributes:
        conn (Connection): Used to access the websocket.
        room: (Room): Room in which the message was sent to.
        msg (str): Raw received message.
        type (str): Type of the received message.
        params (list[str]): Parameters of the received message.
    """

    def __init__(self, room: Room, msg: str) -> None:
        self.conn = room.conn
        self.room = room
        self.msg = msg

    @property
    def _args(self) -> list[str]:
        return self.msg.split("|")

    @property
    def type(self) -> str:
        return self._args[0]

    @property
    def params(self) -> list[str]:
        return self._args[1:]
