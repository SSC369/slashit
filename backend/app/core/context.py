"""The per-request context.

Built once per request and passed to resolvers. ``user_id`` arrives here from a
verified token and nowhere else, which is the mechanism behind FR-6: a caller
cannot attribute work to another user, because no caller supplies the id.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from strawberry.fastapi import BaseContext


@dataclass
class Context(BaseContext):
    """What a resolver may know about the request it is serving.

    Inherits ``BaseContext`` because Strawberry accepts only that or a plain
    dictionary.

    Not frozen, although the index's contract originally said it would be.
    Strawberry assigns ``request`` and ``response`` onto the context object at
    runtime, which a frozen dataclass rejects. Immutability was never the
    mechanism behind FR-6 in any case: the guarantee is that ``user_id`` is only
    ever set in ``build_context`` from a verified token, and no code path takes
    it from caller input.
    """

    user_id: UUID | None
    # Added in 002-authentication slice 1: the `me` query's `Me.email` comes
    # from the verified token, never from a stored row (see identity's
    # graphql/queries.py), so it is carried here the same way user_id is.
    # None whenever user_id is None, and also when a token verified but its
    # payload carried no `email` claim.
    email: str | None
    session: AsyncSession
    request_id: str
    # Added in epic 001 slice 1: a domain whose composition needs its own,
    # independent transaction (the gateway's usage write, AD-8) cannot use
    # ``session`` above, which is shared for the whole request. Most domains
    # use ``session`` directly, per repo-rules.md section 7.4; this exists
    # only for building collaborators that specifically must not share it.
    session_factory: async_sessionmaker[AsyncSession]
    # Added in epic 003 slice 2: a WebSocket's ``connection_init`` payload,
    # which Strawberry assigns here. The bearer token arrives in it, since a
    # browser cannot set headers on a WebSocket.
    connection_params: dict[str, object] | None = None

    @property
    def is_authenticated(self) -> bool:
        """Whether a verified token established an identity."""
        return self.user_id is not None
