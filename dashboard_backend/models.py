from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class UserData(Base):
    __tablename__ = 'user_data'
    discordid = Column(String, primary_key=True)
    discordname = Column(String)
    T1 = Column(String)
    T2 = Column(String)
    T3 = Column(String)
    T4 = Column(String)
    T5 = Column(String)
    T6 = Column(String)
    T7 = Column(String)
    T8 = Column(String)
    T9 = Column(String)
    T10 = Column(String)
    T11 = Column(String)
    T12 = Column(String)
    T13 = Column(String)
    T14 = Column(String)
    T15 = Column(String)
    T16 = Column(String)
    T17 = Column(String)
    T18 = Column(String)

class UserDataHistory(Base):
    __tablename__ = 'user_data_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    discordid = Column(String)
    discordname = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    T1 = Column(String)
    T2 = Column(String)
    T3 = Column(String)
    T4 = Column(String)
    T5 = Column(String)
    T6 = Column(String)
    T7 = Column(String)
    T8 = Column(String)
    T9 = Column(String)
    T10 = Column(String)
    T11 = Column(String)
    T12 = Column(String)
    T13 = Column(String)
    T14 = Column(String)
    T15 = Column(String)
    T16 = Column(String)
    T17 = Column(String)
    T18 = Column(String)

class BotAdmin(Base):
    __tablename__ = 'bot_admins'
    discordid = Column(String, primary_key=True)

class UserStats(Base):
    __tablename__ = 'user_stats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    discordid = Column(String)
    discordname = Column(String)
    game_started = Column(String)
    coins_earned = Column(String)
    cash_earned = Column(String)
    stones_earned = Column(String)
    damage_dealt = Column(String)
    enemies_destroyed = Column(String)
    waves_completed = Column(String)
    upgrades_bought = Column(String)
    workshop_upgrades = Column(String)
    workshop_coins_spent = Column(String)
    research_completed = Column(String)
    lab_coins_spent = Column(String)
    free_upgrades = Column(String)
    interest_earned = Column(String)
    orb_kills = Column(String)
    death_ray_kills = Column(String)
    thorn_damage = Column(String)
    waves_skipped = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) 