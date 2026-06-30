"""Quick test script to verify auth endpoints work locally."""
import asyncio
import sys
from pathlib import Path

# Load .env FIRST
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from app.database.connection import init_db, get_db_session
from app.auth.models import UserDB
from sqlalchemy import select


async def test_auth():
    """Test that we can create a user."""
    print("=== Testing Auth System ===")
    
    # Initialize database
    print("1. Initializing database...")
    await init_db()
    print("   ✓ Database initialized")
    
    # Check if users table exists
    print("\n2. Checking users table...")
    async for session in get_db_session():
        result = await session.execute(select(UserDB).limit(1))
        users = result.scalars().all()
        print(f"   ✓ Users table exists, found {len(users)} user(s)")
        
        # Try to create a test user
        print("\n3. Testing user creation...")
        from app.auth.router import hash_password
        import uuid
        
        test_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        test_user = UserDB(
            id=str(uuid.uuid4()),
            email=test_email,
            hashed_password=hash_password("Test1234!"),
            name="Test User",
            role="patient",
            is_active=True,
        )
        
        session.add(test_user)
        await session.flush()
        await session.commit()
        print(f"   ✓ Test user created: {test_email}")
        
        # Verify the user was created
        result = await session.execute(
            select(UserDB).where(UserDB.email == test_email)
        )
        found_user = result.scalar_one_or_none()
        if found_user:
            print(f"   ✓ User verified in database")
            print(f"     - ID: {found_user.id}")
            print(f"     - Name: {found_user.name}")
            print(f"     - Role: {found_user.role}")
        
        break
    
    print("\n=== All tests passed! ===")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_auth())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
