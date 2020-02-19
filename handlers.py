import json
import requests

import utils

from room import Room

import database


async def add_user(self, roomid, user, skip_avatar_check=False):
    rank = user[0]
    username = user[1:].split("@")[0]
    userid = utils.to_user_id(username)
    idle = user[-2:] == "@!"

    room = Room.get(roomid)

    room.add_user(userid, rank, username, idle)

    if userid == utils.to_user_id(self.username):
        room.roombot = rank == "*"

    db = database.open_db()
    sql = "INSERT INTO utenti (userid, nome) VALUES (?, ?) "
    sql += " ON CONFLICT (userid) DO UPDATE SET nome = excluded.nome"
    db.execute(sql, [userid, username])
    db.connection.commit()
    db.connection.close()

    if not skip_avatar_check or rank != " ":
        await self.send_message("", "/cmd userdetails {}".format(username))


async def remove_user(self, roomid, user):
    Room.get(roomid).remove_user(utils.to_user_id(user))


async def parse_chat_message(self, roomid, user, message):
    if message[: len(self.command_character)] == self.command_character:
        command = message.split(" ")[0][len(self.command_character) :].lower()

        if command in self.commands:
            message = message[
                (len(self.command_character) + len(command) + 1) :
            ].strip()
            await self.commands[command](self, roomid, user, message)
        elif roomid is None:
            await self.send_pm(user, "Invalid command")

    elif roomid is None:
        await self.send_pm(user, "I'm a bot")


async def parse_queryresponse(self, cmd, data):
    data = json.loads(data)
    if cmd == "userdetails":
        userid = data["userid"]
        avatar = str(data["avatar"])
        if avatar in utils.AVATAR_IDS:
            avatar = utils.AVATAR_IDS[avatar]

        db = database.open_db()
        sql = "INSERT INTO utenti (userid, avatar) VALUES (?, ?) "
        sql += " ON CONFLICT (userid) DO UPDATE SET avatar = excluded.avatar"
        db.execute(sql, [userid, avatar])
        db.connection.commit()
        db.connection.close()

        global_rank = data["group"]
        for roomid in data["rooms"]:
            room = Room.get(utils.to_room_id(roomid))
            room_rank = roomid[0] if utils.is_voice(roomid[0]) else " "
            room.set_global_and_room_rank(userid, global_rank, room_rank)


async def init(self, roomid, roomtype):
    pass


async def title(self, roomid, roomtitle):
    Room.get(roomid).title = roomtitle


async def users(self, roomid, userlist):
    for user in userlist.split(",")[1:]:
        await add_user(self, roomid, user, True)


async def join(self, roomid, user):
    await add_user(self, roomid, user)


async def leave(self, roomid, user):
    await remove_user(self, roomid, user)


async def name(self, roomid, user, oldid):
    await remove_user(self, roomid, oldid)
    await add_user(self, roomid, user)


async def chat(self, roomid, user, *message):
    if utils.to_user_id(user) == utils.to_user_id(self.username):
        return
    await parse_chat_message(self, roomid, user, "|".join(message).strip())


async def server_timestamp(self, roomid, timestamp):
    self.timestamp = int(timestamp)


async def timestampchat(self, roomid, timestamp, user, *message):
    if utils.to_user_id(user) == utils.to_user_id(self.username):
        return
    if int(timestamp) <= self.timestamp:
        return
    await parse_chat_message(self, roomid, user, "|".join(message).strip())


async def pm(self, roomid, sender, receiver, *message):
    if utils.to_user_id(sender) == utils.to_user_id(self.username):
        return
    if utils.to_user_id(receiver) != utils.to_user_id(self.username):
        return
    await parse_chat_message(self, None, sender, "|".join(message).strip())


async def challstr(self, roomid, *challstring):
    challstring = "|".join(challstring)

    payload = {
        "act": "login",
        "name": self.username,
        "pass": self.password,
        "challstr": challstring,
    }
    req = requests.post("https://play.pokemonshowdown.com/action.php", data=payload)
    assertion = json.loads(req.text[1:])["assertion"]

    if assertion:
        await self.send_message("", "/trn {},0,{}".format(self.username, assertion))


async def updateuser(self, roomid, user, named, avatar, settings):
    # pylint: disable=too-many-arguments,unused-argument
    username = user.split("@")[0]
    if utils.to_user_id(username) != utils.to_user_id(self.username):
        return

    if avatar != self.avatar:
        await self.send_message("", "/avatar {}".format(self.avatar))

    await self.send_message("", "/status {}".format(self.statustext))

    for public_room in self.rooms:
        await self.send_message("", "/join {}".format(public_room))

    for private_room in self.private_rooms:
        await self.send_message("", "/join {}".format(private_room))


async def formats(self, roomid, *formatslist):
    tiers = []
    section = None
    section_next = False
    for tier in formatslist:
        if tier[0] == ",":
            section_next = True
            continue
        if section_next:
            section = tier
            section_next = False
            continue
        parts = tier.split(",")
        tiers.append({"name": parts[0], "section": section})
    self.tiers = tiers


async def queryresponse(self, roomid, querytype, data):
    await parse_queryresponse(self, querytype, data)


async def tournament(self, roomid, command, *params):
    if command == "create":
        tour_format = params[0]
        await self.commands["sampleteams"](self, roomid, None, tour_format)
