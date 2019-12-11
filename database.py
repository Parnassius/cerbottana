import sqlite3

def open_db():
  db = sqlite3.connect('./database.sqlite')
  db.row_factory = sqlite3.Row
  return db.cursor()
