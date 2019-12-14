from time import time

import utils

class Room:
  _instances = dict()

  def __init__(self, roomid):
    self.roomid = roomid
    self.users = dict()
    self.no_mods_online = None
    self.roombot = False
    self.modchat = False
    self._instances[roomid] = self

  @classmethod
  def get(cls, roomid):
    if roomid in cls._instances:
      return cls._instances[roomid]
    return False

  def add_user(self, userid, rank, username, idle):
    self.users[userid] = {'rank': rank,
                          'username': username,
                          'idle': idle}
    if not idle and utils.is_driver(rank):
      self.no_mods_online = None

  def remove_user(self, userid):
    user = self.users.pop(userid, None)
    if user is not None:
      if utils.is_driver(user['rank']):
        for rank in {self.users[i]['rank'] for i in self.users if not self.users[i]['idle']}:
          if utils.is_driver(rank):
            return
          self.no_mods_online = time()
