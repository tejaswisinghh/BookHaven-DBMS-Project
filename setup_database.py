"""
Database Setup & Initialization Utility
Reads init_db.sql and executes it against the local MySQL instance.
Can be executed as: python setup_database.py
"""

import os
import sys
from pathlib import Path
from config import Config
from db import get_raw_connection, CONNECTOR_TYPE

def initialize_database():
    sql_path = Path(__file__).resolve().parent / "init_db.sql"
    if not sql_path.exists():
        print(f"❌ Error: Could not find '{sql_path}'.")
        sys.exit(1)

    print("=" * 60)
    print(" 🛠️  Online Bookstore Database Initializer")
    print("=" * 60)
    print(f" Host:     {Config.DB_HOST}:{Config.DB_PORT}")
    print(f" User:     {Config.DB_USER}")
    print(f" Database: {Config.DB_NAME}")
    print(f" Driver:   {CONNECTOR_TYPE}")
    print("=" * 60)

    # Read init_db.sql
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    try:
        print("Connecting to MySQL server (without selecting DB)...")
        conn = get_raw_connection(include_database=False)
        cursor = conn.cursor()

        # Split SQL commands by semicolon, ignoring comments
        statements = []
        delimiter = ";"
        current_statement = []

        for line in sql_content.splitlines():
            stripped = line.strip()
            # Ignore full-line comments and empty lines
            if not stripped or stripped.startswith("--") or stripped.startswith("/*"):
                continue

            current_statement.append(line)
            if stripped.endswith(delimiter):
                statement_str = "\n".join(current_statement).strip()
                if statement_str:
                    statements.append(statement_str)
                current_statement = []

        print(f"Found {len(statements)} SQL commands to execute...")
        for i, stmt in enumerate(statements, 1):
            cursor.execute(stmt)

        conn.commit()
        cursor.close()
        conn.close()

        print("\n✅ Success! Database 'BookstoreDB' created and seeded successfully.")
        print("   Tables created: Authors, Customers, Books, Orders")
        print("   Views created:  CustomerOrderSummary, BookSalesSummary")
        print("   Sample records inserted into all tables.")
        print("\nYou can now start the application using:")
        print("   python app.py\n")

    except Exception as exc:
        print(f"\n❌ Error initializing database:\n   {exc}")
        print("\nTroubleshooting tips:")
        print(" 1. Make sure MySQL Server 8.0 is running.")
        print(" 2. Verify root password in '.env' matches your local MySQL setup.")
        print(" 3. Alternatively, you can import 'init_db.sql' manually via MySQL Workbench or command line:")
        print(f'    mysql -u root -p < init_db.sql\n')
        sys.exit(1)

if __name__ == "__main__":
    initialize_database()
