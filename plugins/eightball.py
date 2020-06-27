import random

from plugin_loader import plugin_wrapper
import utils

import database


@plugin_wrapper(helpstr="8ball helpstring")
async def eightball(self, room: str, user: str, arg: str) -> None:
    db = database.open_db()
    answers = db.execute("SELECT risposta FROM eight_ball").fetchall()
    db.connection.close()
    answer = random.choice(answers)["risposta"]
    if answer[0] == "/":
        answer = "/" + answer
    await self.send_reply(room, user, answer)
