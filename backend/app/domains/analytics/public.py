"""The only names other domains may import from analytics.

A domain's public surface is its contract. Adding a name here is a deliberate
act, reviewed like an API change. See backend/.claude/rules/repo-rules.md
section 6.

The published entry point is an interactor rather than a wrapper service, same
reasoning as gateway's public.py: analytics' whole surface is one use case,
and a class that exists only to forward to it would be ceremony.
"""

from app.domains.analytics.interactors.record_event import RecordEventInteractor
from app.domains.analytics.interfaces.dtos import EventType, RecordEventInputDTO

__all__ = [
    "EventType",
    "RecordEventInputDTO",
    "RecordEventInteractor",
]
