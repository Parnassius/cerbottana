# Author: Plato (palt0)


from typing import TYPE_CHECKING

from domify.base_element import BaseElement
from pokedex.enums import Language

from cerbottana import utils

if TYPE_CHECKING:
    from cerbottana.models.room import Room
    from cerbottana.models.user import User


class RawMessage:
    """Raw chat message sent to a room or in PM to a user.

    Attributes:
        conn (Connection): Used to access the websocket.
        room: (Room | None): Room in which the message was sent to. None if the message
            is a PM.
        user (User): Message author.
        message (str): Raw message content.
        language_name (str): Room language if room is not None, defaults to English.
        language_id (int): Veekun id for language.
        language (Language): Pokedex enum for language.
    """

    def __init__(self, room: Room | None, user: User, message: str) -> None:
        # Core attributes
        # Note: `self.conn` should become a property if it's not treated a singleton
        # anymore.
        self.conn = user.conn
        self.room = room
        self.user = user
        self.message = message

    @property
    def language_name(self) -> str:
        if self.room:
            return self.room.language_name
        return "English"

    @property
    def language_id(self) -> int:
        return utils.get_language_id(self.language_name)

    @property
    def language(self) -> Language:
        return Language.get(self.language_name) or Language.get_default()

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
        self,
        message: BaseElement,
        simple_message: str = "",
        *,
        name: str | None = None,
        change: bool = False,
    ) -> None:
        """Sends an HTML box to a room or in PM to a user, depending on the context.

        Args:
            message (BaseElement): HTML to be sent.
            simple_message (str): Alt text, not needed if the HTML box is sent to a
                room. Defaults to a generic message.
            name (str | None): If set, the HTML can be updated by calling this function
                again with the same name. Defaults to None.
            change (bool): True if the HTML should be updated in place, False if the old
                box should be removed and a new one added at the bottom of the chat.
                Ignored if name is None. Defaults to False.
        """
        if self.room is None:
            await self.user.send_htmlbox(
                message, simple_message, name=name, change=change
            )
        else:
            await self.room.send_htmlbox(message, name=name, change=change)

    async def reply_htmlpage(self, pageid: str, room: Room, page: int = 1) -> None:
        """Sends a link to an HTML page to a room or directly to a user, depending on
        the context.

        Args:
            pageid (str): id of the htmlpage.
            room (Room): Room to be passed to the function.
            page (int): Page number. Defaults to 1.
        """
        await self.user.send_htmlpage(pageid, room, page)
        if self.room is not None:
            await self.room.send_htmlpage(pageid, room)


class Message(RawMessage):
    """Chat message sent to a room or in PM to a user.

    Attributes:
        conn (Connection): Used to access the websocket.
        room: (Room | None): Room in which the message was sent to. None if the message
            is a PM.
        user (User): Message author.
        message (str): Raw message content.
        arg (str): Text body of the message without the initial command keyword.
        args (list[str]): arg attribute splitted by commas.
        parametrized_room (Room): See plugins.parametrize_room decorator.
        language_name (str): Room language if room is not None, defaults to English.
        language_id (int): Veekun id for language.
        language (Language): Pokedex enum for language.
    """

    def __init__(self, room: Room | None, user: User, message: str) -> None:
        super().__init__(room, user, message)

        self.arg = self.message.partition(" ")[2].strip()

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
            err = (
                "Trying to access parametrized_room attribute without prior decoration"
            )
            raise AttributeError(err)
        return self._parametrized_room

    @parametrized_room.setter
    def parametrized_room(self, room: Room) -> None:
        self._parametrized_room = room
