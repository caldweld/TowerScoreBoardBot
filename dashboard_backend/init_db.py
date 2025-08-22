#!/usr/bin/env python3
"""
Database initialization script for TowerScoreBoardBot
This script creates all necessary tables and handles schema migrations.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base, UserData, UserDataHistory, BotAdmin, UserStats

# Load environment variables
load_dotenv()

# Database connection
POSTGRES_USER = os.getenv("POSTGRES_USER", "toweruser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "yourpassword")
POSTGRES_DB = os.getenv("POSTGRES_DB", "towerscoreboard")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

def init_database():
    """Initialize the database with all tables"""
    print("🔧 Initializing database...")
    
    # Create engine
    engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,           # validate connection before using
    pool_recycle=1800,            # recycle connections every 30m
    pool_size=5,                  # tune pool sizes
    max_overflow=10,              # allow extra connections when pool is full
    connect_args={                # TCP keepalives for psycopg2
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)
    
    try:
        # Check if user_data table exists and has date column
        with engine.connect() as conn:
            # Check if user_data table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_data'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ user_data table exists")
                
                # Check if date column exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'user_data' 
                        AND column_name = 'date'
                    );
                """))
                date_column_exists = result.scalar()
                
                if not date_column_exists:
                    print("📅 Adding date column to user_data table...")
                    conn.execute(text("""
                        ALTER TABLE user_data 
                        ADD COLUMN date TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                    """))
                    conn.commit()
                    print("✅ date column added successfully")
                else:
                    print("✅ date column already exists")
            else:
                print("📋 Creating all tables...")
                # Create all tables
                Base.metadata.create_all(bind=engine)
                print("✅ All tables created successfully")
        
        print("🎉 Database initialization completed!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise

if __name__ == "__main__":
    init_database() 