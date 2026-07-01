import asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from sqlalchemy import select
from app.database.connection_manager import init_db_with_retry
from app.database.connection import get_engine, get_db_session
from app.auth.models import UserDB

async def main():
    await init_db_with_retry()
    engine = get_engine()
    print("Connected to DB successfully.")
    
    # Get session
    session_generator = get_db_session()
    session = await anext(session_generator)
    
    try:
        result = await session.execute(select(UserDB))
        users = result.scalars().all()
        print(f"Total users: {len(users)}")
        for u in users:
            print(f"- ID: {u.id}, Email: {u.email}, Name: {u.name}, Role: {u.role}, Status: {u.status}")
    finally:
        await session.close()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
