"""The authenticated field, end to end. See 04.2 section 8, case T-2.5."""

from httpx import AsyncClient

ME_QUERY = {"query": "{ me { id } }"}
PUBLIC_QUERY = {"query": "{ apiVersion }"}


async def test_public_field_works_without_a_token(client: AsyncClient) -> None:
    """A field with no permission class stays reachable."""
    response = await client.post("/graphql", json=PUBLIC_QUERY)

    assert response.status_code == 200
    assert response.json()["data"]["apiVersion"] == "0.1.0"


async def test_protected_field_refuses_without_a_token(client: AsyncClient) -> None:
    """T-2.5: IsAuthenticated closes the field before any resolver runs."""
    response = await client.post("/graphql", json=ME_QUERY)
    body = response.json()

    assert body.get("data") is None or body["data"].get("me") is None
    assert body.get("errors"), "an unauthenticated call must produce an error"
    assert "Not authenticated" in str(body["errors"])


async def test_protected_field_refuses_a_garbage_token(client: AsyncClient) -> None:
    """An unverifiable token is the same as no token, and says no more."""
    response = await client.post(
        "/graphql", json=ME_QUERY, headers={"Authorization": "Bearer not.a.token"}
    )
    body = response.json()

    assert body.get("errors")
    assert "Not authenticated" in str(body["errors"])


async def test_refusal_carries_the_unauthenticated_code(client: AsyncClient) -> None:
    """002 T-4.1: the client signs out on this code (FR-23, AD-8), so both a
    missing and an unverifiable token must carry it."""
    for headers in ({}, {"Authorization": "Bearer not.a.token"}):
        response = await client.post("/graphql", json=ME_QUERY, headers=headers)
        errors = response.json()["errors"]

        assert errors[0]["extensions"] == {"code": "UNAUTHENTICATED"}
