from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Message

async def load_full_history(db: AsyncSession, session_id) -> list[dict[str, str]]:
    result = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.created_at, Message.id))
    return [{"role": m.role, "content": m.content} for m in result.scalars().all()]

def apply_sliding_window(history: list[dict[str, str]], max_messages: int) -> list[dict[str, str]]:
    # Trim only LLM context. Never delete persisted database history.
    return history[-max_messages:] if max_messages > 0 else []
