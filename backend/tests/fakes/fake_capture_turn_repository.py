"""An in-memory CaptureTurnRepository."""

import uuid
from datetime import UTC, datetime

from app.domains.capture.interfaces.dtos import (
    CaptureHistoryPageDTO,
    CaptureTurnDTO,
    CaptureTurnOutcome,
)


class FakeCaptureTurnRepository:
    def __init__(self) -> None:
        self.rows: list[CaptureTurnDTO] = []
        # CaptureTurnDTO carries no user_id, matching the real crossing
        # boundary; the fake tracks ownership separately to scope queries.
        self._owner_by_turn_id: dict[uuid.UUID, uuid.UUID] = {}

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
    ) -> None:
        turn = CaptureTurnDTO(
            id=uuid.uuid4(),
            input_text=input_text,
            outcome=outcome,
            resulting_task_id=resulting_task_id,
            resulting_pending_capture_id=resulting_pending_capture_id,
            question_text=question_text,
            answer_text=answer_text,
            created_at=datetime.now(UTC),
            resulting_reminder_id=resulting_reminder_id,
        )
        self.rows.append(turn)
        self._owner_by_turn_id[turn.id] = user_id

    async def list_turns_for_user(
        self, *, user_id: uuid.UUID, cursor: str | None, limit: int
    ) -> CaptureHistoryPageDTO:
        newest_first = sorted(
            (row for row in self.rows if self._owner_by_turn_id.get(row.id) == user_id),
            key=lambda row: row.created_at,
            reverse=True,
        )
        start = 0
        if cursor is not None:
            start = next(
                (
                    index + 1
                    for index, row in enumerate(newest_first)
                    if str(row.id) == cursor
                ),
                len(newest_first),
            )
        page = newest_first[start : start + limit]
        has_more = start + limit < len(newest_first)
        next_cursor = str(page[-1].id) if has_more and page else None
        return CaptureHistoryPageDTO(items=page, next_cursor=next_cursor)
