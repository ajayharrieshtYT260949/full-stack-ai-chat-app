import hashlib
import hmac
from fastapi import Header, HTTPException
from app.config import get_settings

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> str:
    expected = get_settings().chat_api_key
    if not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return hash_api_key(x_api_key)
