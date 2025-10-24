import sqlite3
from pathlib import Path

def main() -> None:
    db_path = Path("d:/arb-bot/dev.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    statements = [
        ("ALTER TABLE config_profiles ADD COLUMN scan_interval_seconds REAL DEFAULT 10.0", "scan_interval_seconds"),
        ("ALTER TABLE config_profiles ADD COLUMN close_interval_seconds REAL DEFAULT 5.0", "close_interval_seconds"),
        ("ALTER TABLE config_profiles ADD COLUMN open_interval_seconds REAL DEFAULT 5.0", "open_interval_seconds"),
    ]

    for stmt, name in statements:
        try:
            cursor.execute(stmt)
            print(f"Added column {name}")
        except sqlite3.OperationalError as exc:  # column may already exist
            if "duplicate column name" in str(exc) or "already exists" in str(exc):
                print(f"Column {name} already exists")
            else:
                raise

    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
