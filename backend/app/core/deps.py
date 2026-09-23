"""The composition root.

The only place a repository, an adapter or a service is constructed, and the
only module allowed to import from more than one domain, because wiring is its
whole job. See backend/.claude/rules/repo-rules.md section 9.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth import decode_email_claim, extract_bearer_token, verify_token
from app.core.context import Context
from app.core.errors import AuthenticationError
from app.core.settings import Settings, get_settings
from app.domains.analytics.interactors.record_event import RecordEventInteractor
from app.domains.analytics.repositories.event_repository import SqlEventRepository
from app.domains.capture.adapters.analytics_event_adapter import (
    CaptureAnalyticsAdapter,
)
from app.domains.capture.adapters.gateway_extraction_adapter import (
    GatewayExtractionAdapter,
)
from app.domains.capture.adapters.identity_clock_adapter import (
    IdentityLocalClockAdapter,
)
from app.domains.capture.adapters.records_task_adapter import RecordsTaskAdapter
from app.domains.capture.adapters.reminders_adapter import RemindersAdapter
from app.domains.capture.interactors.answer_pending_capture import (
    AnswerPendingCaptureInteractor,
)
from app.domains.capture.interactors.discard_pending_capture import (
    DiscardPendingCaptureInteractor,
)
from app.domains.capture.interactors.list_capture_history import (
    ListCaptureHistoryInteractor,
)
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.capture.repositories.capture_turn_repository import (
    SqlCaptureTurnRepository,
)
from app.domains.capture.repositories.pending_capture_repository import (
    SqlPendingCaptureRepository,
)
from app.domains.capture.services.reminder_capture import ReminderCaptureService
from app.domains.gateway.interactors.extract import ExtractInteractor
from app.domains.gateway.repositories.usage_repository import SqlUsageRepository
from app.domains.gateway.services.allowance_service import AllowanceService
from app.domains.gateway.services.langchain_provider import LangChainGeminiProvider
from app.domains.identity.interactors.get_profile import GetProfileInteractor
from app.domains.identity.interactors.get_settings import GetSettingsInteractor
from app.domains.identity.interactors.purge_unverified_accounts import (
    PurgeUnverifiedAccountsInteractor,
)
from app.domains.identity.interactors.sign_in import SignInInteractor
from app.domains.identity.interactors.update_timezone import UpdateTimezoneInteractor
from app.domains.identity.repositories.auth_account_repository import (
    SqlAuthAccountRepository,
)
from app.domains.identity.repositories.auth_attempt_repository import (
    SqlAuthAttemptRepository,
)
from app.domains.identity.repositories.profile_repository import SqlProfileRepository
from app.domains.identity.repositories.settings_repository import SqlSettingsRepository
from app.domains.identity.services.identity_service import IdentityService
from app.domains.identity.services.supabase_auth_service import SupabaseAuthService
from app.domains.notifications.adapters.identity_settings_adapter import (
    IdentityDeliverySettingsAdapter,
)
from app.domains.notifications.interactors.count_unread import CountUnreadInteractor
from app.domains.notifications.interactors.list_notifications import (
    ListNotificationsInteractor,
)
from app.domains.notifications.interactors.mark_all_read import MarkAllReadInteractor
from app.domains.notifications.interactors.mark_notification_read import (
    MarkNotificationReadInteractor,
)
from app.domains.notifications.interactors.stream_notifications import (
    StreamNotificationsInteractor,
)
from app.domains.notifications.repositories.notification_repository import (
    SqlNotificationRepository,
)
from app.domains.notifications.services.live_signal import live_signal
from app.domains.notifications.services.notification_service import (
    NotificationService,
)
from app.domains.records.adapters.analytics_event_adapter import (
    RecordsAnalyticsAdapter,
)
from app.domains.records.adapters.reminders_adapter import ReminderRecordsAdapter
from app.domains.records.interactors.delete_tasks import DeleteTasksInteractor
from app.domains.records.interactors.get_record_detail import GetRecordDetailInteractor
from app.domains.records.interactors.list_tasks import ListTasksInteractor
from app.domains.records.interactors.log_records_view_opened import (
    LogRecordsViewOpenedInteractor,
)
from app.domains.records.interactors.update_task import UpdateTaskInteractor
from app.domains.records.repositories.task_repository import SqlTaskRepository
from app.domains.records.services.records_service import RecordsService
from app.domains.reminders.adapters.identity_clock_adapter import (
    IdentityUserClockAdapter,
)
from app.domains.reminders.adapters.notifications_adapter import NotificationsAdapter
from app.domains.reminders.interactors.create_reminder import CreateReminderInteractor
from app.domains.reminders.interactors.delete_reminder import DeleteReminderInteractor
from app.domains.reminders.interactors.fire_due import FireDueInteractor
from app.domains.reminders.interactors.fire_one import FireOneInteractor
from app.domains.reminders.interactors.get_reminder import GetReminderInteractor
from app.domains.reminders.interactors.list_reminders import ListRemindersInteractor
from app.domains.reminders.interactors.mark_reminder_done import (
    MarkReminderDoneInteractor,
)
from app.domains.reminders.interactors.snooze_reminder import SnoozeReminderInteractor
from app.domains.reminders.interactors.update_reminder import UpdateReminderInteractor
from app.domains.reminders.repositories.reminder_repository import (
    SqlReminderRepository,
)
from app.domains.reminders.services.firing_queue import ProcrastinateFiringQueue
from app.domains.reminders.services.reminder_service import ReminderService


async def build_context(
    *,
    authorization_header: str | None,
    request_id: str,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> Context:
    """Build the per-request context.

    An absent or unusable token produces a context with no identity rather than
    an error. Refusal is a field's decision, made by its permission class, so
    that a public field remains reachable without a token while every other
    field is closed by ``IsAuthenticated``.
    """
    user_id: uuid.UUID | None = None
    email: str | None = None
    token = extract_bearer_token(authorization_header)
    if token is not None:
        try:
            user_id = verify_token(token, settings)
            email = decode_email_claim(token)
        except AuthenticationError:
            user_id = None

    return Context(
        user_id=user_id,
        email=email,
        session=session_factory(),
        request_id=request_id,
        session_factory=session_factory,
    )


def authenticate_connection(
    *, context: Context, authorization_header: str | None
) -> bool:
    """Set a WebSocket's identity from its ``connection_init`` token. The same
    verification an HTTP request gets in ``build_context``; False if it fails."""
    token = extract_bearer_token(authorization_header)
    if token is None:
        return False
    try:
        context.user_id = verify_token(token, get_settings())
        context.email = decode_email_claim(token)
    except AuthenticationError:
        return False
    return True


def build_extract_interactor(
    *, session_factory: async_sessionmaker[AsyncSession], settings: Settings
) -> ExtractInteractor:
    """Wire the gateway.

    This is the only place the provider credential is read, and the only place
    LangChain is named outside the adapter itself. Requirement FR-5: no other
    component holds the key or calls a provider.
    """
    usage_repository = SqlUsageRepository(session_factory)
    return ExtractInteractor(
        provider=LangChainGeminiProvider(
            api_key=settings.gemini_api_key, model=settings.gemini_model
        ),
        usage_repository=usage_repository,
        allowance_service=AllowanceService(usage_repository),
        settings=settings,
    )


def _build_task_port(*, context: Context) -> RecordsTaskAdapter:
    records_service = RecordsService(task_repository=SqlTaskRepository(context.session))
    return RecordsTaskAdapter(records_service=records_service)


def _build_extraction_port(*, context: Context) -> GatewayExtractionAdapter:
    settings = get_settings()
    extract_interactor = build_extract_interactor(
        session_factory=context.session_factory, settings=settings
    )
    return GatewayExtractionAdapter(
        extract_interactor=extract_interactor,
        # Epic 003 AD-7: relative dates read in the user's zone, tasks included.
        local_clock=IdentityLocalClockAdapter(
            identity_service=_build_identity_service(context=context)
        ),
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _build_identity_service(*, context: Context) -> IdentityService:
    return IdentityService(settings_repository=SqlSettingsRepository(context.session))


def _build_user_clock_port(*, context: Context) -> IdentityUserClockAdapter:
    return IdentityUserClockAdapter(
        identity_service=_build_identity_service(context=context)
    )


def build_reminder_service(context: Context) -> ReminderService:
    reminder_repository = SqlReminderRepository(context.session)
    return ReminderService(
        reminder_repository=reminder_repository,
        create_reminder_interactor=CreateReminderInteractor(
            reminder_repository=reminder_repository,
            user_clock=_build_user_clock_port(context=context),
            now_provider=_utc_now,
        ),
    )


def _build_reminder_capture(*, context: Context) -> ReminderCaptureService:
    return ReminderCaptureService(
        reminder_port=RemindersAdapter(
            reminder_service=build_reminder_service(context)
        ),
        extraction=_build_extraction_port(context=context),
    )


def _build_record_event_interactor(*, context: Context) -> RecordEventInteractor:
    return RecordEventInteractor(event_repository=SqlEventRepository(context.session))


def _build_capture_analytics_port(*, context: Context) -> CaptureAnalyticsAdapter:
    return CaptureAnalyticsAdapter(
        record_event_interactor=_build_record_event_interactor(context=context)
    )


def _build_records_analytics_port(*, context: Context) -> RecordsAnalyticsAdapter:
    return RecordsAnalyticsAdapter(
        record_event_interactor=_build_record_event_interactor(context=context)
    )


def build_submit_capture_interactor(context: Context) -> SubmitCaptureInteractor:
    """Wire capture's one use case.

    Epic 001, slice 1 (04.1-capture-core.md). ``capture`` never imports
    ``records`` or ``gateway`` directly; both reach it through a port this
    domain declared and an adapter this function builds, per repo-rules.md
    section 6.
    """
    return SubmitCaptureInteractor(
        pending_capture_repository=SqlPendingCaptureRepository(context.session),
        capture_turn_repository=SqlCaptureTurnRepository(context.session),
        task_port=_build_task_port(context=context),
        extraction=_build_extraction_port(context=context),
        analytics=_build_capture_analytics_port(context=context),
        reminder_port=RemindersAdapter(
            reminder_service=build_reminder_service(context)
        ),
        reminder_capture=_build_reminder_capture(context=context),
    )


def build_answer_pending_capture_interactor(
    context: Context,
) -> AnswerPendingCaptureInteractor:
    return AnswerPendingCaptureInteractor(
        pending_capture_repository=SqlPendingCaptureRepository(context.session),
        capture_turn_repository=SqlCaptureTurnRepository(context.session),
        task_port=_build_task_port(context=context),
        extraction=_build_extraction_port(context=context),
        reminder_capture=_build_reminder_capture(context=context),
    )


def build_discard_pending_capture_interactor(
    context: Context,
) -> DiscardPendingCaptureInteractor:
    return DiscardPendingCaptureInteractor(
        pending_capture_repository=SqlPendingCaptureRepository(context.session),
        capture_turn_repository=SqlCaptureTurnRepository(context.session),
    )


def build_list_capture_history_interactor(
    context: Context,
) -> ListCaptureHistoryInteractor:
    return ListCaptureHistoryInteractor(
        capture_turn_repository=SqlCaptureTurnRepository(context.session)
    )


def build_records_service(context: Context) -> RecordsService:
    """Records' own resolvers may call this directly, the same published
    surface capture's adapter reaches through a port. See 04.2-records-and-
    settings.md section 4: the `tasks` query reuses this, not a new
    interactor, because it is exactly the list `/tasks` already calls."""
    return RecordsService(task_repository=SqlTaskRepository(context.session))


def build_list_tasks_interactor(context: Context) -> ListTasksInteractor:
    return ListTasksInteractor(
        task_repository=SqlTaskRepository(context.session),
        reminder_records=ReminderRecordsAdapter(
            reminder_service=build_reminder_service(context)
        ),
    )


def build_list_reminders_interactor(context: Context) -> ListRemindersInteractor:
    return ListRemindersInteractor(
        reminder_repository=SqlReminderRepository(context.session)
    )


def build_get_reminder_interactor(context: Context) -> GetReminderInteractor:
    return GetReminderInteractor(
        reminder_repository=SqlReminderRepository(context.session)
    )


def build_update_reminder_interactor(context: Context) -> UpdateReminderInteractor:
    return UpdateReminderInteractor(
        reminder_repository=SqlReminderRepository(context.session),
        user_clock=_build_user_clock_port(context=context),
        now_provider=_utc_now,
    )


def build_delete_reminder_interactor(context: Context) -> DeleteReminderInteractor:
    return DeleteReminderInteractor(
        reminder_repository=SqlReminderRepository(context.session)
    )


def build_get_record_detail_interactor(context: Context) -> GetRecordDetailInteractor:
    return GetRecordDetailInteractor(task_repository=SqlTaskRepository(context.session))


def build_update_task_interactor(context: Context) -> UpdateTaskInteractor:
    return UpdateTaskInteractor(task_repository=SqlTaskRepository(context.session))


def build_delete_tasks_interactor(context: Context) -> DeleteTasksInteractor:
    return DeleteTasksInteractor(task_repository=SqlTaskRepository(context.session))


def build_log_records_view_opened_interactor(
    context: Context,
) -> LogRecordsViewOpenedInteractor:
    return LogRecordsViewOpenedInteractor(
        analytics=_build_records_analytics_port(context=context)
    )


def build_get_settings_interactor(context: Context) -> GetSettingsInteractor:
    return GetSettingsInteractor(
        settings_repository=SqlSettingsRepository(context.session)
    )


def build_update_timezone_interactor(context: Context) -> UpdateTimezoneInteractor:
    return UpdateTimezoneInteractor(
        settings_repository=SqlSettingsRepository(context.session)
    )


def build_sign_in_interactor(context: Context) -> SignInInteractor:
    settings = get_settings()
    return SignInInteractor(
        auth_attempt_repository=SqlAuthAttemptRepository(context.session),
        auth_provider=SupabaseAuthService(
            base_url=settings.supabase_url,
            publishable_key=settings.supabase_publishable_key,
        ),
    )


def build_get_profile_interactor(context: Context) -> GetProfileInteractor:
    return GetProfileInteractor(
        profile_repository=SqlProfileRepository(context.session)
    )


def build_purge_unverified_accounts_interactor(
    session: AsyncSession,
) -> PurgeUnverifiedAccountsInteractor:
    """Wired outside a request `Context`: `identity/jobs.py` calls this with
    a session it opened for itself against the service-role connection,
    since a Procrastinate task has no per-request `Context` to draw one
    from."""
    return PurgeUnverifiedAccountsInteractor(
        auth_account_repository=SqlAuthAccountRepository(session)
    )


def _build_notification_service(*, session: AsyncSession) -> NotificationService:
    return NotificationService(
        notification_repository=SqlNotificationRepository(session),
        delivery_settings=IdentityDeliverySettingsAdapter(
            identity_service=IdentityService(
                settings_repository=SqlSettingsRepository(session)
            )
        ),
        now_provider=_utc_now,
    )


def _build_reminder_notifications_port(
    *, session: AsyncSession
) -> NotificationsAdapter:
    return NotificationsAdapter(
        notification_service=_build_notification_service(session=session)
    )


def build_fire_due_interactor(session: AsyncSession) -> FireDueInteractor:
    """Wired outside a request `Context`, for `reminders/jobs.py`."""
    return FireDueInteractor(
        reminder_repository=SqlReminderRepository(session),
        firing_queue=ProcrastinateFiringQueue(),
        now_provider=_utc_now,
    )


def build_fire_one_interactor(session: AsyncSession) -> FireOneInteractor:
    """Wired outside a request `Context`, for `reminders/jobs.py`."""
    return FireOneInteractor(
        reminder_repository=SqlReminderRepository(session),
        notifications=_build_reminder_notifications_port(session=session),
        now_provider=_utc_now,
    )


def build_mark_reminder_done_interactor(context: Context) -> MarkReminderDoneInteractor:
    return MarkReminderDoneInteractor(
        reminder_repository=SqlReminderRepository(context.session),
        notifications=_build_reminder_notifications_port(session=context.session),
        now_provider=_utc_now,
    )


def build_snooze_reminder_interactor(context: Context) -> SnoozeReminderInteractor:
    return SnoozeReminderInteractor(
        reminder_repository=SqlReminderRepository(context.session),
        notifications=_build_reminder_notifications_port(session=context.session),
        user_clock=_build_user_clock_port(context=context),
        now_provider=_utc_now,
    )


def build_list_notifications_interactor(
    context: Context,
) -> ListNotificationsInteractor:
    return ListNotificationsInteractor(
        notification_repository=SqlNotificationRepository(context.session)
    )


def build_count_unread_interactor(context: Context) -> CountUnreadInteractor:
    return CountUnreadInteractor(
        notification_repository=SqlNotificationRepository(context.session)
    )


def build_mark_notification_read_interactor(
    context: Context,
) -> MarkNotificationReadInteractor:
    return MarkNotificationReadInteractor(
        notification_repository=SqlNotificationRepository(context.session),
        now_provider=_utc_now,
    )


def build_mark_all_read_interactor(context: Context) -> MarkAllReadInteractor:
    return MarkAllReadInteractor(
        notification_repository=SqlNotificationRepository(context.session),
        now_provider=_utc_now,
    )


def build_stream_notifications_interactor(
    context: Context,
) -> StreamNotificationsInteractor:
    return StreamNotificationsInteractor(
        notification_repository=SqlNotificationRepository(context.session),
        signal=live_signal,
    )
