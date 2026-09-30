"""hook_password_verification_attempt, hook_before_user_created: the two
Postgres functions Supabase's Auth Hooks call. SQL only — registering them
in a Supabase project's hook configuration is task T-1.4, out of scope here.

Revision ID: 0009_auth_hooks
Revises: 0008_auth_attempts
Create Date: 2026-09-14

FR-17: `hook_password_verification_attempt` runs on Supabase's "Password
Verification Attempt" hook. Input `{"user_id": uuid, "valid": bool}`.
Five failed attempts inside a 15 minute window locks the account for 15
minutes; a valid attempt resets the counter. A currently-locked row rejects
immediately without touching `failed_count` again, so an attacker cannot
extend or shorten the lock by continuing to try.

FR-19: `hook_before_user_created` runs on Supabase's "Before User Created"
hook. Five signups from the same email inside a 1 hour window reject the
6th.

UNVERIFIED PAYLOAD SHAPES: this migration was written without a live
Supabase project to invoke a real hook against. Both functions' exact input
paths and rejection shapes follow Supabase's documented Auth Hook
conventions as understood at the time of writing (an `event` object,
`user_id`/`valid` for password verification, a wrapped `user` object for
before-user-created, `{"decision": ...}` and `{"error": {"message": ...}}`
as the two hook families' respective response shapes) but neither has been
checked against an actual hook invocation. Verify both before T-1.4
registers these against a real project. Flagged again inline, at the two
specific lines this affects.

Rule T2 does not apply here in its usual form: these are functions, not a
table, so there is no RLS to enable. `EXECUTE` is granted narrowly to
`supabase_auth_admin`, the role Supabase runs hooks as, rather than left at
its default (`PUBLIC`).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_auth_hooks"
down_revision: str | None = "0008_auth_attempts"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
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
            """
            CREATE OR REPLACE FUNCTION public.hook_before_user_created(event jsonb)
            RETURNS jsonb
            LANGUAGE plpgsql
            SECURITY DEFINER
            SET search_path = public
            AS $$
            DECLARE
                -- UNVERIFIED: event->'user'->>'email' is the best-documented
                -- guess at this hook's payload shape, not a checked one. See
                -- the module docstring.
                v_email text := event -> 'user' ->> 'email';
                v_row auth_attempts%ROWTYPE;
                v_window interval := interval '1 hour';
            BEGIN
                IF v_email IS NULL THEN
                    RETURN '{}'::jsonb;
                END IF;

                SELECT * INTO v_row FROM auth_attempts
                    WHERE subject = v_email AND kind = 'signup'
                    FOR UPDATE;

                IF NOT FOUND THEN
                    INSERT INTO auth_attempts (
                        id, subject, kind, failed_count, window_started_at,
                        locked_until
                    )
                    VALUES (gen_random_uuid(), v_email, 'signup', 1, now(), NULL);
                    RETURN '{}'::jsonb;
                END IF;

                IF now() - v_row.window_started_at > v_window THEN
                    UPDATE auth_attempts
                        SET failed_count = 1, window_started_at = now()
                        WHERE id = v_row.id;
                    RETURN '{}'::jsonb;
                END IF;

                IF v_row.failed_count + 1 > 5 THEN
                    -- UNVERIFIED: this is the best-documented guess at a
                    -- Before-User-Created rejection shape, not a checked one.
                    -- See the module docstring.
                    RETURN jsonb_build_object(
                        'error', jsonb_build_object(
                            'message',
                            'Too many attempts. Try again in a few minutes.'
                        )
                    );
                END IF;

                UPDATE auth_attempts
                    SET failed_count = v_row.failed_count + 1
                    WHERE id = v_row.id;
                RETURN '{}'::jsonb;
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
    op.execute(
        sa.text(
            "GRANT EXECUTE ON FUNCTION public.hook_before_user_created(jsonb) "
            "TO supabase_auth_admin"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DROP FUNCTION IF EXISTS public.hook_password_verification_attempt(jsonb)"
        )
    )
    op.execute(
        sa.text("DROP FUNCTION IF EXISTS public.hook_before_user_created(jsonb)")
    )
