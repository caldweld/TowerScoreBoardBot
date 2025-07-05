import sqlite3
from sqlalchemy.orm import Session
from models import UserData, UserDataHistory, BotAdmin, Base
from database import engine, SessionLocal

# Connect to SQLite
sqlite_conn = sqlite3.connect("data.db")
sqlite_cur = sqlite_conn.cursor()

# Create tables in PostgreSQL if not already done
Base.metadata.create_all(bind=engine)

# Start PostgreSQL session
db: Session = SessionLocal()

# Migrate user_data
for row in sqlite_cur.execute("SELECT * FROM user_data"):
    db.add(UserData(
        discordid=row[0],
        discordname=row[1],
        **{f"T{i+1}": row[i+2] for i in range(18)}
    ))

# Migrate user_data_history
for row in sqlite_cur.execute("SELECT * FROM user_data_history"):
    db.add(UserDataHistory(
        discordid=row[0],
        discordname=row[1],
        timestamp=row[2],
        **{f"T{i+1}": row[i+3] for i in range(18)}
    ))

# Migrate bot_admins
for row in sqlite_cur.execute("SELECT * FROM bot_admins"):
    db.add(BotAdmin(discordid=row[0]))

db.commit()
db.close()
sqlite_conn.close()
print("Migration complete!")
