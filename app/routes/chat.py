import json
import logging
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import require_api_key
from app.models import ChatSession, Message
from app.schemas import ChatRequest
from app.services.memory_service import load_full_history, apply_sliding_window
from app.services.rate_limit_service import enforce_and_record_message
from app.services.llm_service import stream_completion
from app.services.usage_service import estimate_tokens, calculate_cost
from app.config import get_settings
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["chat"])

@router.post("/{session_id}/chat")
async def chat(session_id: UUID, payload: ChatRequest,
               db: AsyncSession = Depends(get_db),
               key_hash: str = Depends(require_api_key)):
    result = await db.execute(select(ChatSession).where(
        ChatSession.id == session_id, ChatSession.owner_key_hash == key_hash
    ))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    await enforce_and_record_message(db, key_hash)
    db.add(Message(session_id=session_id, role="user", content=payload.message,
                   tokens=estimate_tokens(payload.message)))
    if session.title == "New conversation":
        session.title = payload.message[:60]
    await db.commit()

    full_history = await load_full_history(db, session_id)
    llm_messages = apply_sliding_window(full_history, get_settings().max_history_messages)

    async def event_stream():
        parts = []
        prompt_tokens = completion_tokens = 0
        try:
            async for event in stream_completion(llm_messages):
                if event["type"] == "token":
                    parts.append(event["content"])
                    yield f"data: {json.dumps(event)}\n\n"
                elif event["type"] == "usage":
                    prompt_tokens = event["prompt_tokens"]
                    completion_tokens = event["completion_tokens"]

            answer = "".join(parts)
            if not answer:
                yield f"data: {json.dumps({'type': 'error', 'message': 'The AI service returned an empty response. Please try again.'})}\n\n"
                return
            prompt_tokens = prompt_tokens or estimate_tokens(" ".join(x["content"] for x in llm_messages))
            completion_tokens = completion_tokens or estimate_tokens(answer)
            cost = calculate_cost(prompt_tokens, completion_tokens)

            stored_session = await db.get(ChatSession, session_id)
            if stored_session:
                db.add(Message(session_id=session_id, role="assistant",
                               content=answer, tokens=completion_tokens))
                stored_session.total_prompt_tokens += prompt_tokens
                stored_session.total_completion_tokens += completion_tokens
                stored_session.total_cost_usd += cost
                stored_session.updated_at = datetime.now(timezone.utc)
                await db.commit()

            done = {"type": "done", "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens, "cost_usd": cost}
            yield f"data: {json.dumps(done)}\n\n"
        except Exception:
            logger.exception("AI chat streaming failed for session %s", session_id)

            friendly = {
                "type": "error",
                "message": "Sorry, the AI service is temporarily unavailable. Please try again shortly."
            }

            yield f"data: {json.dumps(friendly)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
