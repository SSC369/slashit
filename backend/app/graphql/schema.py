"""The GraphQL schema.

Domains register their own queries and mutations here as they land; this file
never grows a hand-maintained import list. See backend/rules/repo-rules.md
section 10.
"""

import strawberry

from app.domains.capture.graphql.mutations import CaptureMutations
from app.domains.capture.graphql.queries import CaptureQueries
from app.domains.identity.graphql.mutations import IdentityMutations
from app.domains.identity.graphql.queries import IdentityQueries
from app.domains.records.graphql.mutations import RecordMutations
from app.domains.records.graphql.queries import RecordQueries
from app.domains.reminders.graphql.mutations import ReminderMutations
from app.domains.reminders.graphql.queries import ReminderQueries


@strawberry.type
class Query(CaptureQueries, RecordQueries, IdentityQueries, ReminderQueries):
    """Root query. Each domain's queries class becomes a base here as it
    lands, per section 11: never a hand-maintained field-by-field import."""

    @strawberry.field
    def api_version(self) -> str:
        """Public. A field exists so the schema is valid before any domain ships."""
        return "0.1.0"


@strawberry.type
class Mutation(CaptureMutations, RecordMutations, IdentityMutations, ReminderMutations):
    """Root mutation. Each domain's mutations class becomes a base here as it
    lands, per section 11: never a hand-maintained field-by-field import."""


schema = strawberry.Schema(query=Query, mutation=Mutation)
