"""A LocalDatePort fixed to one day, so period tests read a known today."""

import uuid
from datetime import date


class FakeLocalDatePort:
    def __init__(self, *, today: date) -> None:
        self.today = today

    async def local_today(self, *, user_id: uuid.UUID) -> date:
        return self.today
