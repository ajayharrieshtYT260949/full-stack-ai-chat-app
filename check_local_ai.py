
import asyncio
from openai import AsyncOpenAI
from app.config import get_settings


async def main():
    settings = get_settings()

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url
    )

    try:
        print("Connecting to local Ollama...")

        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "user", "content": "Hello! Introduce yourself."}
            ],
            stream=False
        )

        print("\nLocal AI response:")
        print(response.choices[0].message.content)

        print("\nSUCCESS: Local AI connection works!")

    except Exception as error:
        print("\nLocal AI connection failed:")
        print(type(error).__name__, str(error))

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
