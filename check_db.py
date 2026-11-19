
import asyncio
from sqlalchemy import text
from app.database import engine

async def check_database():
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text("SELECT version()"))
            print("PostgreSQL connection successful!")
            print(result.scalar())

    except Exception as error:
        print("Database connection failed:")
        print(error)

    finally:
        await engine.dispose()

asyncio.run(check_database())
