
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models import Message, RateLimitEvent
from app.dependencies import hash_api_key


H = {"X-API-Key": "test-secret"}


@pytest.mark.asyncio
async def test_auth_required(test_client):
    client, _ = test_client

    response = await client.post("/sessions", json={})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_sessions(test_client):
    client, _ = test_client

    created = await client.post(
        "/sessions",
        headers=H,
        json={"title": "Test"}
    )

    assert created.status_code == 201

    listed = await client.get("/sessions", headers=H)

    assert len(listed.json()) == 1


@pytest.mark.asyncio
async def test_session_isolation(test_client):
    client, _ = test_client

    created = await client.post(
        "/sessions",
        headers=H,
        json={}
    )

    sid = created.json()["id"]

    # Wrong key is rejected and cannot read or delete this session.
    response = await client.get(
        f"/sessions/{sid}/messages",
        headers={"X-API-Key": "wrong"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_21st_request(test_client):
    client, factory = test_client

    created = await client.post(
        "/sessions",
        headers=H,
        json={}
    )

    sid = created.json()["id"]

    async with factory() as db:
        db.add_all([
            RateLimitEvent(
                api_key_hash=hash_api_key("test-secret")
            )
            for _ in range(20)
        ])

        await db.commit()

    response = await client.post(
        f"/sessions/{sid}/chat",
        headers=H,
        json={"message": "blocked"}
    )

    assert response.status_code == 429
    assert response.json()["detail"] == "Rate limit exceeded"
    assert "Retry-After" in response.headers


@pytest.mark.asyncio
async def test_mocked_stream_and_persistence(test_client, monkeypatch):
    from app.routes import chat as chat_route

    async def fake_stream(messages):
        assert messages[-1]["content"] == "hello"

        yield {"type": "token", "content": "Hi "}
        yield {"type": "token", "content": "there"}
        yield {
            "type": "usage",
            "prompt_tokens": 4,
            "completion_tokens": 2
        }

    monkeypatch.setattr(
        chat_route,
        "stream_completion",
        fake_stream
    )

    client, factory = test_client

    created = await client.post(
        "/sessions",
        headers=H,
        json={}
    )

    sid = created.json()["id"]

    response = await client.post(
        f"/sessions/{sid}/chat",
        headers=H,
        json={"message": "hello"}
    )

    assert response.status_code == 200
    assert '"type": "done"' in response.text

    # Convert the session ID string into a UUID for the database query.
    session_uuid = UUID(sid)

    async with factory() as db:
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_uuid)
            .order_by(Message.created_at)
        )

        rows = result.scalars().all()

        assert [message.role for message in rows] == [
            "user",
            "assistant"
        ]

        assert rows[-1].content == "Hi there"


@pytest.mark.asyncio
async def test_delete_session_cascades(test_client):
    client, _ = test_client

    created = await client.post(
        "/sessions",
        headers=H,
        json={}
    )

    sid = created.json()["id"]

    response = await client.delete(
        f"/sessions/{sid}",
        headers=H
    )

    assert response.status_code == 204

    messages_response = await client.get(
        f"/sessions/{sid}/messages",
        headers=H
    )

    assert messages_response.status_code == 404


@pytest.mark.asyncio
async def test_two_sessions_have_isolated_histories(
    test_client,
    monkeypatch
):
    from app.routes import chat as chat_route

    observed = []

    async def fake_stream(messages):
        observed.append([
            item["content"]
            for item in messages
        ])

        yield {"type": "token", "content": "ok"}
        yield {
            "type": "usage",
            "prompt_tokens": 2,
            "completion_tokens": 1
        }

    monkeypatch.setattr(
        chat_route,
        "stream_completion",
        fake_stream
    )

    client, _ = test_client

    first = (
        await client.post(
            "/sessions",
            headers=H,
            json={"title": "First"}
        )
    ).json()["id"]

    second = (
        await client.post(
            "/sessions",
            headers=H,
            json={"title": "Second"}
        )
    ).json()["id"]

    await client.post(
        f"/sessions/{first}/chat",
        headers=H,
        json={"message": "only in first"}
    )

    await client.post(
        f"/sessions/{second}/chat",
        headers=H,
        json={"message": "only in second"}
    )

    assert observed[0] == ["only in first"]
    assert observed[1] == ["only in second"]
