import json

import urllib.request
import urllib.parse

from handler_loader import handler_wrapper
import utils


@handler_wrapper(["challstr"])
async def challstr(self, roomid: str, *challstring: str) -> None:
    payload = "act=login&name={username}&pass={password}&challstr={challstr}".format(
        username=self.username, password=self.password, challstr="|".join(challstring)
    ).encode()

    req = urllib.request.Request(
        "https://play.pokemonshowdown.com/action.php",
        payload,
        {"User-Agent": "Mozilla"},
    )
    resp = urllib.request.urlopen(req)

    assertion = json.loads(resp.read().decode("utf-8")[1:])["assertion"]

    if assertion:
        await self.send_message(
            "", "/trn {},0,{}".format(self.username, assertion), False
        )


@handler_wrapper(["updateuser"])
async def updateuser(
    self, roomid: str, user: str, named: str, avatar: str, settings: str
) -> None:
    username = user.split("@")[0]
    if utils.to_user_id(username) != utils.to_user_id(self.username):
        return

    if avatar != self.avatar:
        await self.send_message("", "/avatar {}".format(self.avatar), False)

    await self.send_message("", "/status {}".format(self.statustext), False)

    for public_room in self.rooms:
        await self.send_message("", "/join {}".format(public_room), False)

    for private_room in self.private_rooms:
        await self.send_message("", "/join {}".format(private_room), False)
