from plugin_loader import Plugin, plugin_wrapper


@plugin_wrapper(is_unlisted=True)
async def help(self, room: str, user: str, arg: str) -> None:
    if arg in self.commands and self.commands[arg].helpstr:
        # asking for a specific command
        message = "<b>{}</b> {}".format(arg, self.commands[arg].helpstr)
        await self.send_htmlbox(room, user, message)
    elif arg == "":
        # asking for a list of every command
        helpstrings = Plugin.get_all_helpstrings()
        if not helpstrings:
            return

        html = ""
        for key in helpstrings:
            html += "<b>{}</b> {}<br>".format(key, helpstrings[key])
        await self.send_htmlbox(room, user, html[:-4])
