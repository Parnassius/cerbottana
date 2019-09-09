class Room:
  _instances = dict()

  def __init__(self, roomid):
    self.roomid = roomid
    self.users = dict()
    self.roombot = False
    self._instances[roomid] = self

  @classmethod
  def get(self, roomid):
    if roomid in self._instances:
      return self._instances[roomid]
    else:
      return False

  def addUser(self, userid, rank, username):
    self.users[userid] = {'rank': rank,
                        'username': username}

  def removeUser(self, user):
    self.users.pop(user, None)
