import database
import os

from plugin_loader import plugin_wrapper
import utils

from room import Room


def create_token(self, rank: str) -> str:
    token_id = os.urandom(16).hex()

    db = database.open_db()
    sql = "INSERT INTO tokens (token, rank, scadenza) VALUES (?, ?, DATETIME('now', '+1 minute'))"
    db.execute(sql, [token_id, rank])
    db.connection.commit()
    db.connection.close()

    return token_id


@plugin_wrapper(aliases=["dashboard"])
async def token(self, room: str, user: str, arg: str) -> None:
    userid = utils.to_user_id(user)
    for room in self.rooms:
        users = Room.get(room).users
        if userid in users and utils.is_driver(users[userid]["rank"]):
            rank = users[userid]["rank"]
            break
    else:
        return

    token_id = create_token(self, rank)

    await self.send_pm(
        user, "{url}?token={token}".format(url=os.environ["DOMAIN"], token=token_id)
    )
