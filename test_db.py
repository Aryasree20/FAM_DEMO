import asyncio

from sqlalchemy import text

from app.db.session import engine


async def test():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            print("DATABASE CONNECTION SUCCESS:", result.scalar())
    except Exception as e:
        print("DATABASE CONNECTION FAILED:")
        print(type(e).__name__)
        print(e)


asyncio.run(test())