"""Implements capture's ExtractionPort against the gateway domain."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.domains.capture.interfaces.ports import LocalClockPort
from app.domains.gateway.public import (
    ExtractInteractor,
    ExtractionRequest,
    ExtractionResult,
)


class GatewayExtractionAdapter:
    def __init__(
        self,
        *,
        extract_interactor: ExtractInteractor,
        local_clock: LocalClockPort | None = None,
    ) -> None:
        self.extract_interactor = extract_interactor
        self.local_clock = local_clock

    async def extract(
        self,
        *,
        user_id: UUID,
        prompt: str,
        schema: dict[str, Any],
        instruction: str,
    ) -> ExtractionResult:
        # Kept short deliberately: constants.py documents why instruction and
        # schema description length measurably affect generation latency
        # against the 8 second budget.
        reference = await self._reference_moment(user_id=user_id)
        full_instruction = f"{instruction} {reference}"
        return await self.extract_interactor.extract(
            user_id=user_id,
            request=ExtractionRequest(
                prompt=prompt, schema=schema, instruction=full_instruction
            ),
        )

    async def _reference_moment(self, *, user_id: UUID) -> str:
        """Epic 003 AD-7: "tomorrow" means tomorrow where the user is. Before
        this, every relative date resolved against server UTC. The local time
        carries its offset, so an ISO answer resolved from it is correct."""
        if self.local_clock is None:
            return f"Today is {datetime.now(UTC).isoformat()}."
        local_now, timezone_name = await self.local_clock.local_now(user_id=user_id)
        return f"Now is {local_now.isoformat()} ({timezone_name})."
