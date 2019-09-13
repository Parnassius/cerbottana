class Room:
  _instances = dict()

  def __init__(self, roomid):
    self.roomid = roomid
    self.users = dict()
    self.roombot = False
    self._instances[roomid] = self

  @classmethod
  def get(cls, roomid):
    if roomid in cls._instances:
      return cls._instances[roomid]
    return False

  def add_user(self, userid, rank, username):
    self.users[userid] = {'rank': rank,
                          'username': username}

  def remove_user(self, user):
    self.users.pop(user, None)
