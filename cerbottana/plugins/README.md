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

To invoke a command, just type in the chat one of its associated strings, preceded by the env variable `COMMAND_CHARACTER`.

The preferred way to inizialize a `Command` instance is through the `command_wrapper` decorator, which acts as a functional interface to the class constructor.

Here is the structure of a plugin module with one command, where every parameter of the decorator is optional:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from . import command_wrapper

if TYPE_CHECKING:
    from cerbottana.models.message import Message


@command_wrapper(
    aliases=("other name1", "other name2"),
    helpstr="Describes the foo command.",
    #is_unlisted=True
)
async def foo(msg: Message) -> None:
    pass
```

`aliases` is the `tuple[str]` parameter that populates the dictionary of commands; the decorated function name is automatically included as an alias.

A `Command` object can also yield useful metadata: `helpstr` is a string that describes the callback function. It is used to generate a help document with data from every instance that doesn't have the boolean parameter `is_unlisted` explicitly set to `True`.
