import type { AuthError } from "@supabase/supabase-js";
import { AlertCircle, Check } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent, type ReactElement } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";

import { supabaseClient } from "../../../../api/lib/supabaseClient";
import Button from "../../../../design-system/components/Button";
import { cn } from "../../../../utils/cn";
import AuthCard from "../../components/AuthCard";
import OtpInput from "../../components/OtpInput";
import * as Styles from "./styles";

const OTP_LENGTH = 6;

// NFR-4: Supabase's native per-account OTP-send limit is 60s; this cooldown
// mirrors VerifyEmailController's so the two code screens behave alike. It is
// a UI affordance only — the real limit is enforced server-side.
const RESEND_COOLDOWN_SECONDS = 30;

const SIGN_IN_REDIRECT_DELAY_MS = 1600;

// Supabase's own throttles, matched the same way SignUpController's
// classifySignUpError does after its 2026-09-15 live correction: error.code
// first, HTTP status only as a fallback, because a 400 was observed for the
// same throttle condition.
const RATE_LIMIT_ERROR_CODES = new Set(["over_email_send_rate_limit", "over_request_rate_limit"]);
const RATE_LIMIT_STATUS = 429;

// 02-design.md §4/§8: the reset flow shows ONE message for both a mistyped and
// an expired code, since a reset code is single-use either way (NFR-2). That
// makes this screen immune to the wrong-vs-expired ambiguity logged against
// VerifyEmailController on 2026-09-15 (Supabase returns `otp_expired` for
// both, so that screen's WRONG branch is dead code). Here the two collapse by
// design, not by accident.
const CODE_ERROR_MESSAGE = "This code is wrong or has expired. Request a new one.";

// 04.2 §6's last row ("Network failure, any call") calls for "a generic
// retry-safe error" without giving wording.
// > Assumption: reusing SignUpController's generic wording verbatim so the
// > auth screens do not diverge; flag for the design owner if different copy
// > is wanted.
const GENERIC_ERROR_MESSAGE = "Something went wrong. Try again.";

// Supabase rejects a password below the project's minimum length or strength
// with this documented code (@supabase/auth-js ErrorCode union). Its own
// message names the actual rule ("Password should be at least N characters"),
// which the project owner can change in the dashboard, so it is shown as-is
// rather than duplicated as a Slashit string that would silently go stale.
// 02-design.md gives no copy for this case.
// > Assumption: surfacing Supabase's wording here, marked for the design
// > owner.
const WEAK_PASSWORD_ERROR_CODE = "weak_password";

// 02-design.md gives no copy for a mismatched or empty new password; the
// canvas draws the password step in its resting state only.
// > Assumption: wording invented here, marked for the design owner.
const PASSWORD_MISMATCH_MESSAGE = "Both passwords must match.";
const PASSWORD_EMPTY_MESSAGE = "Enter a new password.";

type StepType = "CODE" | "PASSWORD";
type ViewStateType = "FORM" | "LOADING" | "LIMITED" | "SUCCESS";

interface LocationState {
  email?: string;
}

const formatCooldown = (seconds: number): string => `0:${String(seconds).padStart(2, "0")}`;

const isRateLimitError = (error: AuthError): boolean => {
  const hasKnownCode = error.code !== undefined && RATE_LIMIT_ERROR_CODES.has(error.code);
  return hasKnownCode || error.status === RATE_LIMIT_STATUS;
};

const ResetPasswordController = (): ReactElement => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  const emailFromQuery = searchParams.get("email");
  const emailFromState = (location.state as LocationState | null)?.email ?? null;
  const email = emailFromQuery ?? emailFromState ?? null;
  const hasEmail = email !== null;

  const [step, setStep] = useState<StepType>("CODE");
  const [viewState, setViewState] = useState<ViewStateType>("FORM");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [cooldownSeconds, setCooldownSeconds] = useState(RESEND_COOLDOWN_SECONDS);

  const codeRef = useRef(code);
  codeRef.current = code;

  useEffect(() => {
    const intervalId = setInterval(() => {
      setCooldownSeconds((seconds) => (seconds > 0 ? seconds - 1 : 0));
    }, 1000);
    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    const isSuccess = viewState === "SUCCESS";
    if (!isSuccess) return undefined;
    const timeoutId = window.setTimeout(() => {
      navigate("/sign-in", { replace: true });
    }, SIGN_IN_REDIRECT_DELAY_MS);
    return () => window.clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewState]);

  const handleVerifyCode = async (submittedCode: string): Promise<void> => {
    const isSubmittable = email !== null && submittedCode.length === OTP_LENGTH;
    if (!isSubmittable) return;

    setErrorMessage(null);
    setViewState("LOADING");

    const { error } = await supabaseClient.auth.verifyOtp({
      email,
      token: submittedCode,
      type: "recovery",
    });

    const isStillCurrentSubmission = codeRef.current === submittedCode;
    if (!isStillCurrentSubmission) return;

    if (!error) {
      // verifyOtp with type "recovery" opens a real session, which is what
      // updateUser needs on the next step. It is closed again on success,
      // below, so the flow exits to Sign in as 02-design.md §3 draws it.
      setStep("PASSWORD");
      setViewState("FORM");
      return;
    }

    if (isRateLimitError(error)) {
      setViewState("LIMITED");
      return;
    }

    setErrorMessage(CODE_ERROR_MESSAGE);
    setViewState("FORM");
  };

  const handleCodeChange = (value: string): void => {
    setCode(value);
    const isComplete = value.length === OTP_LENGTH;
    if (isComplete) void handleVerifyCode(value);
  };

  const handleContinueClick = (): void => {
    void handleVerifyCode(code);
  };

  const handleResend = async (): Promise<void> => {
    if (email === null) return;
    setErrorMessage(null);
    setCode("");
    setCooldownSeconds(RESEND_COOLDOWN_SECONDS);
    await supabaseClient.auth.resetPasswordForEmail(email);
  };

  const handleSetPassword = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();

    const isPasswordEmpty = password.length === 0;
    if (isPasswordEmpty) {
      setErrorMessage(PASSWORD_EMPTY_MESSAGE);
      return;
    }

    const doPasswordsMatch = password === confirmPassword;
    if (!doPasswordsMatch) {
      setErrorMessage(PASSWORD_MISMATCH_MESSAGE);
      return;
    }

    setErrorMessage(null);
    setViewState("LOADING");

    const { error } = await supabaseClient.auth.updateUser({ password });

    if (error) {
      const isWeakPassword = error.code === WEAK_PASSWORD_ERROR_CODE;
      setErrorMessage(isWeakPassword ? error.message : GENERIC_ERROR_MESSAGE);
      setViewState("FORM");
      return;
    }

    // The recovery session opened by verifyOtp is closed here: FR-13's flow
    // ends at Sign in with the new password, not signed straight in.
    await supabaseClient.auth.signOut();
    setViewState("SUCCESS");
  };

  const isLoading = viewState === "LOADING";
  const hasError = errorMessage !== null;
  const isResendAvailable = cooldownSeconds <= 0;
  const isContinueDisabled = !hasEmail || code.length !== OTP_LENGTH || isLoading;
  const isMismatch = errorMessage === PASSWORD_MISMATCH_MESSAGE;
  const subtitle =
    email !== null ? (
      <>
        We sent a 6-digit code to <span className={Styles.emailStyles}>{email}</span>
      </>
    ) : (
      "We sent a 6-digit code to your email."
    );

  if (viewState === "SUCCESS") {
    return (
      <AuthCard>
        <div className={Styles.centerCardStyles}>
          <div className={Styles.successIconStyles}>
            <Check size={24} />
          </div>
          <div className={Styles.centerTitleStyles}>Password changed</div>
          <div className={Styles.statusBodyStyles}>Sign in with your new password.</div>
        </div>
      </AuthCard>
    );
  }

  if (viewState === "LIMITED") {
    return (
      <AuthCard>
        <div className={Styles.centerCardStyles}>
          <div className={Styles.warnIconStyles}>
            <AlertCircle size={24} />
          </div>
          <div className={Styles.centerTitleStyles}>Too many attempts</div>
          <div className={Styles.statusBodyStyles}>
            This code is now blocked. Request a new one in 15 minutes.
          </div>
        </div>
      </AuthCard>
    );
  }

  if (step === "PASSWORD") {
    return (
      <AuthCard>
        <div className={Styles.titleStyles}>Set a new password</div>
        <div className={Styles.subtitleStyles}>
          Email verified. Choose a new password for your account.
        </div>

        {hasError ? (
          <div className={Styles.noteErrorStyles} role="alert">
            <AlertCircle size={16} className={Styles.noteErrorIconStyles} />
            <div>{errorMessage}</div>
          </div>
        ) : null}

        <form onSubmit={handleSetPassword} noValidate>
          <div className={Styles.formRowStyles}>
            <label className={Styles.fieldLabelStyles} htmlFor="reset-password-new">
              New password
            </label>
            <input
              id="reset-password-new"
              type="password"
              autoComplete="new-password"
              disabled={isLoading}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="••••••••••"
              className={Styles.controlStyles}
            />
          </div>

          <div className={Styles.lastFormRowStyles}>
            <label className={Styles.fieldLabelStyles} htmlFor="reset-password-confirm">
              Confirm new password
            </label>
            <input
              id="reset-password-confirm"
              type="password"
              autoComplete="new-password"
              disabled={isLoading}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="••••••••••"
              aria-invalid={isMismatch}
              className={cn(Styles.controlStyles, isMismatch && Styles.controlErrorStyles)}
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
            className={Styles.submitButtonStyles}
          >
            {isLoading ? (
              <>
                <span className={Styles.spinnerStyles} />
                <span>Saving&hellip;</span>
              </>
            ) : (
              <span>Set new password</span>
            )}
          </Button>
        </form>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      footer={
        <>
          Need a new code?{" "}
          <Link to="/forgot-password" className={Styles.footerLinkStyles}>
            Start over
          </Link>
        </>
      }
    >
      <div className={Styles.centerTitleStyles}>Enter the code</div>
      <div className={Styles.centerSubtitleStyles}>{subtitle}</div>

      {hasError ? (
        <div className={Styles.noteErrorStyles} role="alert">
          <AlertCircle size={16} className={Styles.noteErrorIconStyles} />
          <div>{errorMessage}</div>
        </div>
      ) : null}

      <OtpInput
        value={code}
        onChange={handleCodeChange}
        error={hasError}
        disabled={isLoading || !hasEmail}
        autoFocus
      />

      <div className={Styles.resendRowStyles} aria-live="polite">
        {isResendAvailable ? (
          <button
            type="button"
            className={Styles.resendLinkStyles}
            disabled={!hasEmail}
            onClick={() => void handleResend()}
          >
            Resend code
          </button>
        ) : (
          <span>Resend code in {formatCooldown(cooldownSeconds)}</span>
        )}
      </div>

      <Button
        type="button"
        variant="primary"
        className={Styles.submitButtonStyles}
        disabled={isContinueDisabled}
        onClick={handleContinueClick}
      >
        {isLoading ? (
          <>
            <span className={Styles.spinnerStyles} />
            <span>Checking&hellip;</span>
          </>
        ) : (
          <span>Continue</span>
        )}
      </Button>
    </AuthCard>
  );
};

export default ResetPasswordController;
