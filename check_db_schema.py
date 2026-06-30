"""Check the actual database schema for users table."""
import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from app.database.connection import get_db_session
from sqlalchemy import text


async def check_schema():
    """Check users table schema."""
    from app.database.connection import init_db
    await init_db()
    
    async for session in get_db_session():
        # Check column types
        result = await session.execute(text("""
            SELECT column_name, data_type, udt_name, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))
        
        print("=== Users Table Schema ===")
        for row in result:
            print(f"{row[0]:<20} {row[1]:<15} {row[2]:<15} {row[3] or ''}")
        
        # Check if userrole enum exists
        result = await session.execute(text("""
            SELECT typname, enum_range(NULL::userrole) AS enum_values
            FROM pg_type
            WHERE typname = 'userrole'
        """))
        
        enum_row = result.fetchone()
        if enum_row:
            print(f"\n=== ENUM Type 'userrole' EXISTS ===")
            print(f"Values: {enum_row[1]}")
        else:
            print(f"\n=== NO ENUM Type 'userrole' ===")
        
        break


if __name__ == "__main__":
    asyncio.run(check_schema())
