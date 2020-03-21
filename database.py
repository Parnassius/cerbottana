import sqlite3


def open_db() -> sqlite3.Cursor:
    db = sqlite3.connect("./database.sqlite")
    db.row_factory = sqlite3.Row
    return db.cursor()
