from __future__ import annotations

import random
from typing import TYPE_CHECKING

from sqlalchemy.orm import Query
from sqlalchemy.orm.exc import ObjectDeletedError

import databases.database as d
from database import Database
from plugins import command_wrapper, htmlpage_wrapper

if TYPE_CHECKING:
    from models.message import Message
    from models.room import Room
    from models.user import User


@command_wrapper(aliases=("8ball",), helpstr="Chiedi qualsiasi cosa!")
async def eightball(msg: Message) -> None:
    db = Database.open()

    with db.get_session() as session:
        language_name = msg.language
        if language_name not in DEFAULT_ANSWERS:
            language_name = "English"
        answers = DEFAULT_ANSWERS[language_name]

        if msg.room:
            custom_answers = (
                session.query(d.EightBall).filter_by(roomid=msg.room.roomid).all()
            )
            answers.extend([i.answer for i in custom_answers])

        await msg.reply(random.choice(answers))


@command_wrapper(
    aliases=("8ballanswers",), required_rank="driver", parametrize_room=True
)
async def eightballanswers(msg: Message) -> None:
    try:
        page = int(msg.arg)
    except ValueError:
        page = 1

    await msg.user.send_htmlpage("eightball", msg.parametrized_room, page)


@command_wrapper(
    aliases=("add8ballanswer", "neweightballanswer", "new8ballanswer"),
    required_rank="driver",
    parametrize_room=True,
)
async def addeightballanswer(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Cosa devo salvare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = d.EightBall(answer=msg.arg, roomid=msg.parametrized_room.roomid)
        session.add(result)
        session.commit()

        try:
            if result.id:
                await msg.reply("Risposta salvata.")
                if msg.room is None:
                    await msg.parametrized_room.send_modnote(
                        "EIGHTBALL ANSWER ADDED", msg.user, msg.arg
                    )
                return
        except ObjectDeletedError:
            pass
        await msg.reply("Risposta già esistente.")


@command_wrapper(
    aliases=(
        "remove8ballanswer",
        "deleteeightballanswer",
        "delete8ballanswer",
        "deleightballanswer",
        "del8ballanswer",
        "rmeightballanswer",
        "rm8ballanswer",
    ),
    required_rank="driver",
    parametrize_room=True,
)
async def removeeightballanswer(msg: Message) -> None:
    if not msg.arg:
        await msg.reply("Che risposta devo cancellare?")
        return

    db = Database.open()
    with db.get_session() as session:
        result = (
            session.query(d.EightBall)
            .filter_by(answer=msg.arg, roomid=msg.parametrized_room.roomid)
            .delete()
        )
        if result:
            await msg.reply("Risposta cancellata.")
            if msg.room is None:
                await msg.parametrized_room.send_modnote(
                    "EIGHTBALL ANSWER REMOVED", msg.user, msg.arg
                )
        else:
            await msg.reply("Risposta inesistente.")


@command_wrapper(required_rank="driver", parametrize_room=True)
async def removeeightballanswerid(msg: Message) -> None:
    if len(msg.args) != 2:
        return

    db = Database.open()
    with db.get_session() as session:
        query = session.query(d.EightBall).filter_by(
            id=msg.args[0], roomid=msg.parametrized_room.roomid
        )
        answer = query.first()
        if answer:
            if msg.room is None:
                await msg.parametrized_room.send_modnote(
                    "EIGHTBALL ANSWER REMOVED", msg.user, answer.answer
                )
            query.delete()

    try:
        page = int(msg.args[1])
    except ValueError:
        page = 1

    await msg.user.send_htmlpage("eightball", msg.parametrized_room, page)


@htmlpage_wrapper("eightball", required_rank="driver")
def eightball_htmlpage(user: User, room: Room) -> Query:  # type: ignore[type-arg]
    return Query(d.EightBall).filter_by(roomid=room.roomid).order_by(d.EightBall.answer)


DEFAULT_ANSWERS = {
    "French": [
        "Essaye plus tard",
        "Essaye encore",
        "Pas d'avis",
        "C'est ton destin",
        "Le sort en est jeté",
        "Une chance sur deux",
        "Repose ta question",
        "D'après moi oui",
        "C'est certain",
        "Oui absolument",
        "Tu peux compter dessus",
        "Sans aucun doute",
        "Très probable",
        "Oui",
        "C'est bien parti",
        "C'est non",
        "Peu probable",
        "Faut pas rêver",
        "N'y compte pas",
        "Impossible",
    ],
    "German": [
        "Zeichen deuten auf ja",
        "Ja",
        "Ohne einen Zweifel",
        "Wie ich es sehe ja",
        "Höchstwahrscheinlich",
        "Darauf kannst du dich verlassen",
        "Definitiv ja",
        "Es ist so entschieden",
        "Gute Aussichten",
        "Es ist sicher",
        "Antwort unklar, versuchs nochmal",
        "Konzentriere dich und frag nochmal",
        "Ich sags dir jetzt lieber nicht",
        "Kann es jetzt nicht vorhersagen",
        "Frag später nochmal",
        "Meine Quellen sagen nein",
        "Sehr zweifelhaft",
        "Zähl nicht drauf",
        "Nicht so gute Aussichten",
        "Meine Antwort ist nein",
    ],
    "Spanish": [
        "En mi opinión, sí",
        "Es cierto",
        "Es decididamente así",
        "Probablemente",
        "Buen pronóstico",
        "Todo apunta a que sí",
        "Sin duda",
        "Sí",
        "Sí - definitivamente",
        "Debes confiar en ello",
        "Respuesta vaga, vuelve a intentarlo",
        "Pregunta en otro momento",
        "Será mejor que no te lo diga ahora",
        "No puedo predecirlo ahora",
        "Concéntrate y vuelve a preguntar",
        "Puede ser",
        "No cuentes con ello",
        "Mi respuesta es no",
        "Mis fuentes me dicen que no",
        "Las perspectivas no son buenas",
        "Muy dudoso",
    ],
    "Italian": [
        "Per quanto posso vedere, sì",
        "È certo",
        "È decisamente così",
        "Molto probabilmente",
        "Le prospettive sono buone",
        "I segni indicano di sì",
        "Senza alcun dubbio",
        "Sì",
        "Sì, senza dubbio",
        "Ci puoi contare",
        "È difficile rispondere, prova di nuovo",
        "Rifai la domanda più tardi",
        "Meglio non risponderti adesso",
        "Non posso predirlo ora",
        "Concentrati e rifai la domanda",
        "Non ci contare",
        "La mia risposta è no",
        "Le mie fonti dicono di no",
        "Le prospettive non sono buone",
        "Molto incerto",
    ],
    "English": [
        "It is certain",
        "It is decidedly so",
        "Without a doubt",
        "Yes - definitely",
        "You may rely on it",
        "As I see it, yes",
        "Most likely",
        "Outlook good",
        "Yes",
        "Signs point to yes",
        "Reply hazy, try again",
        "Ask again later",
        "Better not tell you now",
        "Cannot predict now",
        "Concentrate and ask again",
        "Don't count on it",
        "My reply is no",
        "My sources say no",
        "Outlook not so good",
        "Very doubtful",
    ],
}
