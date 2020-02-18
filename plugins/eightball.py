import random

import utils

import database


async def eightball(self, room, user, arg):
    if room is not None and not utils.is_voice(user):
        return

    db = database.open_db()
    answers = db.execute("SELECT risposta FROM eight_ball").fetchall()
    db.connection.close()
    answer = random.choice(answers)["risposta"]
    if answer[0] == "/":
        answer = "/" + answer
    await self.send_reply(room, user, answer)


commands = {"8ball": eightball, "eightball": eightball}
