# Plugins

Plugins are Python modules that extend the bot's base functionalities by adding new commands.

## Adding new commands

A `Command` class instance represents a dictionary of strings that are bound to the same callback function.
For example the `addquote` command represents:

```python
{
    "addquote": plugins.quotes.addquote,
    "newquote": plugins.quotes.addquote,
    "quote": plugins.quotes.addquote
}
```

To invoke a command it suffices to write one of its associated strings, preceded by the env variable `COMMAND_CHARACTER`, in the chat.

The preferred way to inizialize a `Command` instance is through the `command_wrapper` decorator, that acts as a functional interface to the class constructor.

Here's the structure of a plugin module with one command (every parameter of the decorator is optional):

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from plugins import command_wrapper

if TYPE_CHECKING:
    from connection import Connection


@command_wrapper(
    aliases=["other name1", "other name2"],
    helpstr="Describes the foo command.",
    #is_unlisted=True
)
async def foo(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    pass
```

`aliases` is the `List[str]` parameter that populates the dictionary of commands; the decorated function's name is automatically included as an alias.

A `Command` object can also yield useful metadata: `helpstr` is a string that describes the callback function. It is used to generate a help document with data from every instance that doesn't have the boolean parameter `is_unlisted` explicitly set to `False`.

## Generating Flask webpages
A plugin module might add some routes to the Flask server created in `server.py`. Use the `route_wrapper` decorator with the same syntax of a regular Flask route decorator and put any needed template files in the `../templates/` folder.

The most common use case is linking a webpage with a command:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from plugins import command_wrapper, route_wrapper

if TYPE_CHECKING:
    from connection import Connection


@route_wrapper("/foo")
def foo(room: str) -> str:
    return render_template("foo.html")

@command_wrapper()
async def linkfoo(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    await conn.send_reply(room, user, f"{conn.domain}foo")
```
