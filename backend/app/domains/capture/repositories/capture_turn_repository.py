"""The only SQL for capture_turns. Returns DTOs, never models."""

import base64
import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import literal, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.capture.interfaces.dtos import (
    CaptureHistoryPageDTO,
    CaptureTurnDTO,
    CaptureTurnOutcome,
)
from app.domains.capture.models import CaptureTurn


def _encode_cursor(*, created_at: datetime, turn_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{turn_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(*, cursor: str) -> tuple[datetime, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    created_at_text, turn_id_text = raw.split("|", 1)
    return datetime.fromisoformat(created_at_text), uuid.UUID(turn_id_text)


def _turn_to_dto(*, turn: CaptureTurn) -> CaptureTurnDTO:
    return CaptureTurnDTO(
        id=turn.id,
        input_text=turn.input_text,
        outcome=cast(CaptureTurnOutcome, turn.outcome),
        resulting_task_id=turn.resulting_task_id,
        resulting_pending_capture_id=turn.resulting_pending_capture_id,
        question_text=turn.question_text,
        answer_text=turn.answer_text,
        created_at=turn.created_at,
        resulting_reminder_id=turn.resulting_reminder_id,
        resulting_memory_id=turn.resulting_memory_id,
    )


class SqlCaptureTurnRepository:
    """Against the request's own session, same pattern as task_repository.py."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_turn(
        self,
        *,
        user_id: uuid.UUID,
        input_text: str,
        outcome: CaptureTurnOutcome,
        resulting_task_id: uuid.UUID | None,
        resulting_pending_capture_id: uuid.UUID | None,
        question_text: str | None,
        answer_text: str | None,
        resulting_reminder_id: uuid.UUID | None = None,
        resulting_memory_id: uuid.UUID | None = None,
    ) -> None:
        async with user_transaction(self.session, user_id) as scoped:
            scoped.add(
                CaptureTurn(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    input_text=input_text,
                    outcome=outcome,
                    resulting_task_id=resulting_task_id,
                    resulting_pending_capture_id=resulting_pending_capture_id,
                    resulting_reminder_id=resulting_reminder_id,
                    resulting_memory_id=resulting_memory_id,
                    question_text=question_text,
                    answer_text=answer_text,
                    created_at=datetime.now(UTC),
                )
            )

    async def list_turns_for_user(
        self, *, user_id: uuid.UUID, cursor: str | None, limit: int
    ) -> CaptureHistoryPageDTO:
        statement = (
            select(CaptureTurn)
            .where(CaptureTurn.user_id == user_id)
            .order_by(CaptureTurn.created_at.desc(), CaptureTurn.id.desc())
            .limit(limit + 1)
        )
        if cursor is not None:
            cursor_created_at, cursor_id = _decode_cursor(cursor=cursor)
            statement = statement.where(
                tuple_(CaptureTurn.created_at, CaptureTurn.id)
                < tuple_(literal(cursor_created_at), literal(cursor_id))
            )

        async with user_transaction(self.session, user_id) as scoped:
            result = await scoped.scalars(statement)
            turns = result.all()

        has_more = len(turns) > limit
        page = turns[:limit]
        next_cursor = (
            _encode_cursor(created_at=page[-1].created_at, turn_id=page[-1].id)
            if has_more
            else None
        )
        return CaptureHistoryPageDTO(
            items=[_turn_to_dto(turn=turn) for turn in page],
            next_cursor=next_cursor,
        )
