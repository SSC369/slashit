"""The only names other domains may import from identity.

Epic 003 publishes the reminder settings (index §4). Adding a name here is a
deliberate act, reviewed like an API change; see
backend/.claude/rules/repo-rules.md section 6.2.
"""

from app.domains.identity.interfaces.dtos import ReminderSettingsDTO
from app.domains.identity.services.identity_service import IdentityService

__all__ = ["IdentityService", "ReminderSettingsDTO"]
