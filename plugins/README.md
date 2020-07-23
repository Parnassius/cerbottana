Plugins are additional groups of handlers that extend the bot's base functionalities.

A `Plugin` class instance represents a dictionary of command strings that are bound to the same callback function.
For example the `shitpost` plugin represents:
```python
{
    "meme": plugins.shitpost,
    "memes": plugins.shitpost,
    "mims": plugins.shitpost,
    "say": plugins.shitpost
}
```

The preferred way to inizialize a `Plugin` instance is through the `plugin_wrapper` decorator, that acts as a functional interface to the class constructor.

Here's the structure of a file with one plugin (every parameter of the decorator is optional):
```python
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from connection import Connection

from plugins import plugin_wrapper


@plugin_wrapper(
    aliases=["other name1", "other name2"],
    helpstr="Describes the foo plugin.",
    #is_unlisted=True
)
async def foo(conn: Connection, room: Optional[str], user: str, arg: str) -> None:
    pass

# no need to put the function in a dict here even with multiple functions
```

`aliases` is the `List[str]` parameter that populates the dictionary of commands; the decorated function's name is automatically included as an alias.

A `Plugin` object can also yield useful metadata: `helpstr` is a string that describes the callback function. It is used to generate a help document with data from every instance that doesn't have the boolean parameter `is_unlisted` explicitly set to `False`.
