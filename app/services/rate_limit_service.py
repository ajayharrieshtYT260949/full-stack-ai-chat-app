
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import RateLimitEvent


async def enforce_and_record_message(
    db: AsyncSession,
    api_key_hash: str
) -> None:
    cfg = get_settings()

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(
        seconds=cfg.rate_limit_window_seconds
    )

    count = await db.scalar(
        select(func.count(RateLimitEvent.id)).where(
            RateLimitEvent.api_key_hash == api_key_hash,
            RateLimitEvent.created_at >= cutoff
        )
    )

    if (count or 0) >= cfg.rate_limit_messages:

        oldest = await db.scalar(
            select(RateLimitEvent.created_at).where(
                RateLimitEvent.api_key_hash == api_key_hash,
                RateLimitEvent.created_at >= cutoff
            ).order_by(
                RateLimitEvent.created_at
            ).limit(1)
        )

        # SQLite may return a naive datetime even when
        # timezone=True is configured on the SQLAlchemy column.
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=timezone.utc)
        else:
            oldest = oldest.astimezone(timezone.utc)

        retry_after = max(
            1,
            int(
                (
                    oldest
                    + timedelta(seconds=cfg.rate_limit_window_seconds)
                    - now
                ).total_seconds()
            )
        )

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )

    db.add(
        RateLimitEvent(api_key_hash=api_key_hash)
    )

    await db.flush()
