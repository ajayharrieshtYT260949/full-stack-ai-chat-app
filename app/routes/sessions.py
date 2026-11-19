from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import require_api_key
from app.models import ChatSession, Message
from app.schemas import SessionCreate, SessionOut, MessageOut

router = APIRouter(prefix="/sessions", tags=["sessions"])

async def get_owned_session(db: AsyncSession, session_id: UUID, key_hash: str) -> ChatSession:
    result = await db.execute(select(ChatSession).where(
        ChatSession.id == session_id, ChatSession.owner_key_hash == key_hash
    ))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(payload: SessionCreate, db: AsyncSession = Depends(get_db),
                         key_hash: str = Depends(require_api_key)):
    session = ChatSession(owner_key_hash=key_hash, title=payload.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db), key_hash: str = Depends(require_api_key)):
    result = await db.execute(select(ChatSession).where(
        ChatSession.owner_key_hash == key_hash
    ).order_by(ChatSession.updated_at.desc()))
    return result.scalars().all()

@router.get("/{session_id}/messages", response_model=list[MessageOut])
async def get_messages(session_id: UUID, db: AsyncSession = Depends(get_db),
                       key_hash: str = Depends(require_api_key)):
    await get_owned_session(db, session_id, key_hash)
    result = await db.execute(select(Message).where(
        Message.session_id == session_id
    ).order_by(Message.created_at, Message.id))
    return result.scalars().all()

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db),
                         key_hash: str = Depends(require_api_key)):
    session = await get_owned_session(db, session_id, key_hash)
    await db.delete(session)
    await db.commit()
