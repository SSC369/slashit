"""SQLAlchemy tables for identity. Nothing else lives here.

The foreign key to ``auth.users`` is declared in the migration, not here, for
the same reason ``records.models`` does it that way (AD-9, no local mirror of
Supabase's ``auth`` schema).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class UserSettings(Base):
    """One row per user. Created on first read, per FR-28."""

    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    timezone: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Profile(Base):
    """One row per user, a 1:1 extension of ``auth.users``.

    Created by the ``handle_new_user()`` trigger at signup (migration
    0007_profiles), never here. The primary key is the user's own id, not a
    ``user_id`` foreign key column, which is why it is named ``id``.
    """

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuthAttempt(Base):
    """Rate-limit state for sign-in and signup (migration 0008_auth_attempts).

    One row per (subject, kind). For ``sign_in``, ``subject`` is now an
    email, not a user id: FR-17's lockout moved from a Supabase hook (which
    only ran once Supabase had already resolved the user) into the app,
    which knows the email before any lookup. ``signup`` rows are still
    written by the ``hook_before_user_created`` hook directly in SQL, never
    through this model.
    """

    __tablename__ = "auth_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    subject: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    failed_count: Mapped[int] = mapped_column(Integer)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
