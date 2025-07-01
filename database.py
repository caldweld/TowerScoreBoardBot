import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="data.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            discordid TEXT PRIMARY KEY,
            discordname TEXT,
            T1 TEXT, T2 TEXT, T3 TEXT, T4 TEXT, T5 TEXT, T6 TEXT,
            T7 TEXT, T8 TEXT, T9 TEXT, T10 TEXT, T11 TEXT, T12 TEXT,
            T13 TEXT, T14 TEXT, T15 TEXT, T16 TEXT, T17 TEXT, T18 TEXT
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data_history (
            discordid TEXT,
            discordname TEXT,
            timestamp TEXT,
            T1 TEXT, T2 TEXT, T3 TEXT, T4 TEXT, T5 TEXT, T6 TEXT,
            T7 TEXT, T8 TEXT, T9 TEXT, T10 TEXT, T11 TEXT, T12 TEXT,
            T13 TEXT, T14 TEXT, T15 TEXT, T16 TEXT, T17 TEXT, T18 TEXT
        )
        """)
        self.conn.commit()

    def save_user_data(self, discord_id, discord_name, tier_data):
        values = [discord_id, discord_name] + tier_data
        placeholders = ','.join(['?'] * len(values))
        self.cursor.execute(f"""
            INSERT OR REPLACE INTO user_data (
                discordid, discordname,
                T1, T2, T3, T4, T5, T6,
                T7, T8, T9, T10, T11, T12,
                T13, T14, T15, T16, T17, T18
            ) VALUES ({placeholders})
        """, values)

        timestamp = datetime.utcnow().isoformat()
        values_with_time = [discord_id, discord_name, timestamp] + tier_data
        placeholders_hist = ','.join(['?'] * len(values_with_time))

        # Check if identical record exists
        self.cursor.execute("""
            SELECT 1 FROM user_data_history
            WHERE discordid = ? AND T1 = ? AND T2 = ? AND T3 = ? AND T4 = ? AND T5 = ? AND T6 = ? AND
                  T7 = ? AND T8 = ? AND T9 = ? AND T10 = ? AND T11 = ? AND T12 = ? AND
                  T13 = ? AND T14 = ? AND T15 = ? AND T16 = ? AND T17 = ? AND T18 = ?
        """, [discord_id] + tier_data)

        if not self.cursor.fetchone():
            self.cursor.execute(f"""
                INSERT INTO user_data_history (
                    discordid, discordname, timestamp,
                    T1, T2, T3, T4, T5, T6,
                    T7, T8, T9, T10, T11, T12,
                    T13, T14, T15, T16, T17, T18
                ) VALUES ({placeholders_hist})
            """, values_with_time)

        self.conn.commit()

    def get_user_data(self, discord_id):
        self.cursor.execute("SELECT T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18 FROM user_data WHERE discordid = ?", (discord_id,))
        return self.cursor.fetchone()

    def get_all_user_data(self):
        self.cursor.execute("SELECT * FROM user_data")
        return self.cursor.fetchall()

    def get_all_user_data_history(self):
        self.cursor.execute("SELECT * FROM user_data_history")
        return self.cursor.fetchall()

    def get_all_users(self):
        self.cursor.execute("SELECT discordname, T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17, T18 FROM user_data")
        return self.cursor.fetchall()

    def get_tier_for_all_users(self, tier_num):
        self.cursor.execute(f"SELECT discordname, T{tier_num} FROM user_data")
        return self.cursor.fetchall() 