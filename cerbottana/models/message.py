# Author: Plato (palt0)

from __future__ import annotations

from typing import TYPE_CHECKING

from domify.base_element import BaseElement

from cerbottana import utils

from .room import Room
from .user import User

if TYPE_CHECKING:
    from cerbottana.connection import Connection


class Message:
    """Chat message sent to a room or in PM to a user.

    Attributes:
        conn (Connection): Used to access the websocket.
        room: (Room | None): Room in which the message was sent to. None if the message
            is a PM.
        user (User): Message author.
        arg (str): Text body of the message without the initial command keyword.
        args (list[str]): arg attribute splitted by commas.
        parametrized_room (Room): See plugins.parametrize_room decorator.
        language (str): Room language if room is not None, defaults to English.
        language_id (int): Veekun id for language.
    """

    def __init__(self, room: Room | None, user: User, arg: str) -> None:
        # Core attributes
        # Note: `self.conn` should become a property if it's not treated a singleton
        # anymore.
        self.conn = user.conn
        self.room = room
        self.user = user
        self.arg = arg

        # Attributes to support supplementary functionalities
        self._parametrized_room: Room | None = None

    @property
    def args(self) -> list[str]:
        # Special case to preserve msg.arg's truth.
        # An empty string (False) would be translated to [""] (True).
        if not self.arg:
            return []

        return [word.strip() for word in self.arg.split(",")]

    @args.setter
    def args(self, new: list[str]) -> None:
        self.arg = ",".join(new)

    @property
    def parametrized_room(self) -> Room:
        if self._parametrized_room is None:
            raise AttributeError(
                "Trying to access parametrized_room attribute without prior decoration"
            )
        return self._parametrized_room

    @parametrized_room.setter
    def parametrized_room(self, room: Room) -> None:
        self._parametrized_room = room

    @property
    def language(self) -> str:
        if self.room:
            return self.room.language
        return "English"

    @property
    def language_id(self) -> int:
        return utils.get_language_id(self.language)

    async def reply(self, message: str, escape: bool = True) -> None:
        """Sends a text message to a room or in PM to a user, depending on the context.

        Args:
            message (str): Text to be sent.
            escape (bool): True if PS commands should be escaped. Defaults to True.
        """
        if self.room is None:
            await self.user.send(message, escape)
        else:
            await self.room.send(message, escape)

    async def reply_htmlbox(
        self, message: BaseElement, simple_message: str = ""
    ) -> None:
        """Sends an HTML box to a room or in PM to a user, depending on the context.

        Args:
            message (BaseElement): HTML to be sent.
            simple_message (str): Alt text, not needed if the HTML box is sent to a
                room. Defaults to a generic message.
        """
        if self.room is None:
            await self.user.send_htmlbox(message, simple_message)
        else:
            await self.room.send_htmlbox(message)

    async def reply_htmlpage(self, pageid: str, room: Room, page: int = 1) -> None:
        """Sends a link to an HTML page to a room or directly to a user, depending on
        the context.

        Args:
            pageid (str): id of the htmlpage.
            room (Room): Room to be passed to the function.
            page (int): Page number. Defaults to 1.
        """
        if self.room is None:
            await self.user.send_htmlpage(pageid, room, page)
        else:
            await self.room.send_htmlpage(pageid, room)
