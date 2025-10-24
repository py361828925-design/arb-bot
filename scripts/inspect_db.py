import sqlite3

conn = sqlite3.connect("d:/arb-bot/dev.db")
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("tables:", tables)
