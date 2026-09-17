import type { AuthError } from "@supabase/supabase-js";
import { AlertCircle, Check } from "lucide-react";
import { useState, type ChangeEvent, type FormEvent, type ReactElement } from "react";
import { Link } from "react-router";

import { supabaseClient } from "../../../../api/lib/supabaseClient";
import Button from "../../../../design-system/components/Button";
import { cn } from "../../../../utils/cn";
import AuthCard from "../../components/AuthCard";
import * as Styles from "./styles";

// Format validation only. 02-design.md §4 is explicit that this screen never
// says "no account with that email" — that would leak account enumeration,
// the same reasoning FR-11 applies to Sign in. The only client-side rejection
// is a malformed address.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Supabase's own throttles on sending a reset email. Both codes are from
// @supabase/auth-js's ErrorCode union, and `over_email_send_rate_limit` is the
// one confirmed live against this project during slice 1 (see 05-dev-log.md's
// 2026-09-15 follow-up on classifySignUpError): the HTTP status for it was not
// reliably 429, so error.code is matched first and status kept as a fallback.
const RATE_LIMIT_ERROR_CODES = new Set(["over_email_send_rate_limit", "over_request_rate_limit"]);
const RATE_LIMIT_STATUS = 429;

// 04.2-password-reset.md §6's last row ("Network failure, any call") calls for
// "a generic retry-safe error" without giving wording, and 02-design.md §8's
// copy table does not cover it either.
// > Assumption: reusing SignUpController's generic wording verbatim so the two
// > screens do not diverge; flag for the design owner if different copy is
// > wanted.
const GENERIC_ERROR_MESSAGE = "Something went wrong. Try again.";

const INVALID_EMAIL_MESSAGE = "Enter a valid email address.";

// The canvas draws a field-level line under the input reading "Missing the
// domain part", for the address `jordan@example`. That is the one case it
// specifies, so it is shown for exactly that case and omitted otherwise
// rather than inventing a second message.
const MISSING_DOMAIN_MESSAGE = "Missing the domain part";

type ViewStateType = "FORM" | "LOADING" | "LIMITED" | "SUCCESS";
type ErrorKindType = "NONE" | "INVALID_EMAIL" | "GENERIC";

const isMissingDomainPart = (email: string): boolean => {
  const [, domain] = email.split("@");
  const hasDomain = domain !== undefined && domain.length > 0;
  return hasDomain && !domain.includes(".");
};

const isRateLimitError = (error: AuthError): boolean => {
  const hasKnownCode = error.code !== undefined && RATE_LIMIT_ERROR_CODES.has(error.code);
  return hasKnownCode || error.status === RATE_LIMIT_STATUS;
};

const ForgotPasswordController = (): ReactElement => {
  const [email, setEmail] = useState("");
  const [viewState, setViewState] = useState<ViewStateType>("FORM");
  const [errorKind, setErrorKind] = useState<ErrorKindType>("NONE");

  const handleEmailChange = (event: ChangeEvent<HTMLInputElement>): void => {
    setEmail(event.target.value);
    setErrorKind("NONE");
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();

    const trimmedEmail = email.trim();
    const isEmailWellFormed = EMAIL_PATTERN.test(trimmedEmail);
    if (!isEmailWellFormed) {
      setErrorKind("INVALID_EMAIL");
      return;
    }

    setErrorKind("NONE");
    setViewState("LOADING");

    const { error } = await supabaseClient.auth.resetPasswordForEmail(trimmedEmail);

    if (!error) {
      // Deliberately the same confirmation whether or not an account exists.
      // Supabase's resetPasswordForEmail does not distinguish the two, and
      // this screen must not either (FR-12, T-2.2).
      setViewState("SUCCESS");
      return;
    }

    if (isRateLimitError(error)) {
      setViewState("LIMITED");
      return;
    }

    setErrorKind("GENERIC");
    setViewState("FORM");
  };

  const isLoading = viewState === "LOADING";
  const hasError = errorKind !== "NONE";
  const isInvalidEmail = errorKind === "INVALID_EMAIL";
  const shouldShowMissingDomain = isInvalidEmail && isMissingDomainPart(email.trim());
  const bannerMessage = isInvalidEmail ? INVALID_EMAIL_MESSAGE : GENERIC_ERROR_MESSAGE;

  if (viewState === "SUCCESS") {
    return (
      <AuthCard
        footer={
          <>
            Have the code already?{" "}
            <Link
              to={`/reset-password?email=${encodeURIComponent(email.trim())}`}
              className={Styles.footerLinkStyles}
            >
              Enter it now
            </Link>
          </>
        }
      >
        <div className={Styles.centerCardStyles}>
          <div className={Styles.successIconStyles}>
            <Check size={24} />
          </div>
          <div className={Styles.titleStyles}>Check your email</div>
          <div className={Styles.statusBodyStyles}>
            If an account exists for that address, we have sent a code to reset the password.
          </div>
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
          <div className={Styles.titleStyles}>Too many requests</div>
          <div className={Styles.statusBodyStyles}>
            Too many reset requests for this address. Try again in a few minutes.
          </div>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      footer={
        <>
          Remembered it?{" "}
          <Link to="/sign-in" className={Styles.footerLinkStyles}>
            Back to sign in
          </Link>
        </>
      }
    >
      <div className={Styles.titleStyles}>Reset your password</div>
      <div className={Styles.subtitleStyles}>
        Enter your email and we will send a code to reset it.
      </div>

      {hasError ? (
        <div className={Styles.noteErrorStyles} role="alert">
          <AlertCircle size={16} className={Styles.noteErrorIconStyles} />
          <div>{bannerMessage}</div>
        </div>
      ) : null}

      <form onSubmit={handleSubmit} noValidate>
        <div className={Styles.formRowStyles}>
          <label className={Styles.fieldLabelStyles} htmlFor="forgot-password-email">
            Email
          </label>
          <input
            id="forgot-password-email"
            type="email"
            autoComplete="email"
            disabled={isLoading}
            value={email}
            onChange={handleEmailChange}
            placeholder="jordan@example.com"
            aria-invalid={isInvalidEmail}
            className={cn(Styles.controlStyles, isInvalidEmail && Styles.controlErrorStyles)}
          />
          {shouldShowMissingDomain ? (
            <div className={Styles.fieldErrorStyles}>{MISSING_DOMAIN_MESSAGE}</div>
          ) : null}
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
              <span>Sending&hellip;</span>
            </>
          ) : (
            <span>Send code</span>
          )}
        </Button>
      </form>
    </AuthCard>
  );
};

export default ForgotPasswordController;
