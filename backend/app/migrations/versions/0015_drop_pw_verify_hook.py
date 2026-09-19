"""Drop hook_password_verification_attempt: unusable on this project's plan.

Revision ID: 0015_drop_pw_verify_hook
Revises: 0014_events
Create Date: 2026-09-19

Named short deliberately: Alembic's default `alembic_version.version_num` is
`VARCHAR(32)`, and this migration's first attempt at a revision id
(`0015_drop_password_verification_hook`, 36 characters) overran it. The
`upgrade()` transaction rolled back cleanly when that write failed — Alembic
wraps the DDL and the version-table update in one transaction — but it is
the reason this id is short. Caught live, applying to the real project;
worth checking future ids against this limit rather than by feel.

User decision 2026-09-19: Supabase's Password Verification Attempt hook is
Teams/Enterprise only (confirmed against the live dashboard, which shows only
Send SMS, Send Email, Custom Access Token and Before User Created). FR-17's
lockout moves into the app instead: a new `identity.interactors.sign_in`
replaces the direct `supabaseClient.auth.signInWithPassword` call, and a new
`AuthAttemptRepository` re-implements this function's counting logic in
Python against the same `auth_attempts` table, keyed by email rather than
user id (the app knows the email before any user lookup; the hook only knew
a user id because Supabase itself had already resolved one).

The function can never be registered as a hook on this plan and its
user-id-keyed logic no longer matches how `auth_attempts` is used for
`sign_in` rows, so it is dropped rather than left as dead code.
`hook_before_user_created` (FR-19) is untouched: that hook is available and
stays registered.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015_drop_pw_verify_hook"
down_revision: str | None = "0014_events"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "DROP FUNCTION IF EXISTS public.hook_password_verification_attempt(jsonb)"
        )
    )


def downgrade() -> None:
    # Recreated verbatim from 0009_auth_hooks.py, for a clean downgrade path.
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.hook_password_verification_attempt(
                event jsonb
            )
            RETURNS jsonb
            LANGUAGE plpgsql
            SECURITY DEFINER
            SET search_path = public
            AS $$
            DECLARE
                v_user_id uuid := (event ->> 'user_id')::uuid;
                v_valid boolean := (event ->> 'valid')::boolean;
                v_row auth_attempts%ROWTYPE;
                v_window interval := interval '15 minutes';
            BEGIN
                SELECT * INTO v_row FROM auth_attempts
                    WHERE subject = v_user_id::text AND kind = 'sign_in'
                    FOR UPDATE;

                IF NOT FOUND THEN
                    INSERT INTO auth_attempts (
                        id, subject, kind, failed_count, window_started_at,
                        locked_until
                    )
                    VALUES (
                        gen_random_uuid(), v_user_id::text, 'sign_in', 0, now(), NULL
                    )
                    RETURNING * INTO v_row;
                END IF;

                IF v_row.locked_until IS NOT NULL AND v_row.locked_until > now() THEN
                    RETURN jsonb_build_object(
                        'decision', 'reject',
                        'message', 'Too many attempts. Try again in 15 minutes.'
                    );
                END IF;

                IF v_valid THEN
                    UPDATE auth_attempts
                        SET failed_count = 0, locked_until = NULL
                        WHERE id = v_row.id;
                    RETURN jsonb_build_object('decision', 'continue');
                END IF;

                IF now() - v_row.window_started_at > v_window THEN
                    UPDATE auth_attempts
                        SET failed_count = 1, window_started_at = now(),
                            locked_until = NULL
                        WHERE id = v_row.id;
                    RETURN jsonb_build_object('decision', 'continue');
                END IF;

                IF v_row.failed_count + 1 >= 5 THEN
                    UPDATE auth_attempts
                        SET failed_count = v_row.failed_count + 1,
                            locked_until = now() + v_window
                        WHERE id = v_row.id;
                    RETURN jsonb_build_object(
                        'decision', 'reject',
                        'message', 'Too many attempts. Try again in 15 minutes.'
                    );
                END IF;

                UPDATE auth_attempts
                    SET failed_count = v_row.failed_count + 1
                    WHERE id = v_row.id;
                RETURN jsonb_build_object('decision', 'continue');
            END;
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            "GRANT EXECUTE ON FUNCTION "
            "public.hook_password_verification_attempt(jsonb) "
            "TO supabase_auth_admin"
        )
    )
