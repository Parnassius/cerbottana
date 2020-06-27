from plugin_loader import plugin_wrapper
import utils


@plugin_wrapper(helpstr="Che dire, un comando molto figo, toh ti ho aiutato.")
async def colorcompare(self, room: str, user: str, arg: str) -> None:
    if arg == "":
        return

    cell = "<td>"
    cell += '  <div style="background:{color};text-align:center"><br><br>{username}<br><br><br></div>'
    cell += "</td>"

    html = '<table style="width:100%;table-layout:fixed">'
    html += "<tr>"
    for i in arg.split(","):
        html += cell.format(
            color=utils.username_color(utils.to_user_id(i)),
            username=utils.html_escape(i),
        )
    html += "</tr>"
    html += "</table>"

    await self.send_htmlbox(room, user, html)
