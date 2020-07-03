from typing import Optional, Any, Dict

from time import time

import utils


class Room:
    _instances = dict()  # type: Dict[str, Room]

    def __init__(self, roomid: str) -> None:
        self.roomid = roomid
        self.users: Dict[str, Dict[str, Any]] = dict()
        self.no_mods_online: Optional[float] = None
        self.roombot = False
        self.modchat = False
        self._instances[roomid] = self

    @classmethod
    def get(cls, roomid: str):
        if roomid not in cls._instances:
            Room(roomid)
        return cls._instances[roomid]

    def add_user(self, userid: str, rank: str, username: str, idle: bool) -> None:
        self.users[userid] = {
            "rank": rank,
            "global_rank": None,
            "room_rank": None,
            "username": username,
            "idle": idle,
        }
        if utils.is_driver(rank):
            if not idle:
                self.no_mods_online = None
            else:
                self.check_no_mods_online()

    def remove_user(self, userid: str) -> None:
        user = self.users.pop(userid, None)
        if user is not None:
            if utils.is_driver(user["rank"]):
                self.check_no_mods_online()

    def set_global_and_room_rank(
        self, userid: str, global_rank: str, room_rank: str
    ) -> None:
        if userid in self.users:
            self.users[userid]["global_rank"] = global_rank
            self.users[userid]["room_rank"] = room_rank

    def check_no_mods_online(self) -> None:
        if self.no_mods_online:
            return
        for user in self.users:
            if self.users[user]["idle"]:
                continue
            rank = self.users[user]["room_rank"] or self.users[user]["rank"]
            if utils.is_driver(rank):
                return
        self.no_mods_online = time()
