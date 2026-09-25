import { CheckIcon, CircleAlertIcon } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent, type ReactElement } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import useSignIn from "../../../../api/mutations/SignIn/useSignIn";
import { supabaseClient } from "../../../../api/lib/supabaseClient";
import Button from "../../../../design-system/components/Button";
import { readReturnPath } from "../../../../utils/returnPath";
import AuthCard from "../../components/AuthCard";
import * as Styles from "./styles";

const SUCCESS_REDIRECT_DELAY_MS = 1200;
const BLOCKED_REDIRECT_DELAY_MS = 1600;

type ViewStateType =
  | "FORM"
  | "LOADING"
  | "ERROR"
  | "BLOCKED"
  | "LIMITED"
  | "UNAVAILABLE"
  | "SUCCESS";

// Google's official four-colour "G" mark. Copied verbatim from
// process-docs/002-authentication/assets/canvas/SignIn.dc.html per the
// design spec; a fixed brand mark, not a themeable value, so it is exempt
// from the no-raw-colour rule the rest of this file follows.
const GoogleGMark = (): ReactElement => (
  <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
    <path
      fill="#4285F4"
      d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"
    />
    <path
      fill="#34A853"
      d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
    />
    <path
      fill="#FBBC05"
      d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
    />
    <path
      fill="#EA4335"
      d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
    />
  </svg>
);

const SignInController = (): ReactElement => {
  const navigate = useNavigate();
  const location = useLocation();
  const returnPath = readReturnPath(location.search);
  const { triggerAPI: triggerSignIn } = useSignIn();
  const [viewState, setViewState] = useState<ViewStateType>("FORM");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const redirectTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (redirectTimeoutRef.current !== null) window.clearTimeout(redirectTimeoutRef.current);
    };
  }, []);

  const handleGoogleSignIn = async (): Promise<void> => {
    await supabaseClient.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin + returnPath,
        // Google silently re-authenticates on an existing browser session
        // with prior consent, skipping the account chooser. Forcing it
        // keeps "Continue with Google" honest about which account is used.
        queryParams: { prompt: "select_account" },
      },
    });
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    setViewState("LOADING");

    // FR-17's lockout is enforced by the backend (identity.SignInInteractor),
    // not a Supabase Auth Hook: that hook is Teams/Enterprise only, confirmed
    // against the live project 2026-09-19. This mutation is the sign-in path
    // now; supabaseClient only receives the resulting session.
    triggerSignIn({
      email,
      password,
      onSignedIn: async (session) => {
        await supabaseClient.auth.setSession({
          access_token: session.accessToken,
          refresh_token: session.refreshToken,
        });
        setViewState("SUCCESS");
        redirectTimeoutRef.current = window.setTimeout(
          () => navigate(returnPath),
          SUCCESS_REDIRECT_DELAY_MS,
        );
      },
      onAccountNotVerified: () => {
        setViewState("BLOCKED");
        redirectTimeoutRef.current = window.setTimeout(
          () => navigate(`/verify-email?email=${encodeURIComponent(email)}`),
          BLOCKED_REDIRECT_DELAY_MS,
        );
      },
      onAccountLocked: () => setViewState("LIMITED"),
      onProviderUnavailable: () => setViewState("UNAVAILABLE"),
      // Wrong password and an unregistered email land here too, and render
      // the same byte-identical copy either way (FR-11): there is only one
      // branch that can produce this state, so the wording cannot diverge
      // by cause.
      onInvalidCredentials: () => setViewState("ERROR"),
      onRequestFailed: () => setViewState("UNAVAILABLE"),
    });
  };

  const isLoading = viewState === "LOADING";
  const isError = viewState === "ERROR";

  if (viewState === "SUCCESS") {
    return (
      <AuthCard>
        <div className={Styles.centerCardStyles}>
          <div className={Styles.successIconStyles}>
            <CheckIcon size={24} />
          </div>
          <div className={Styles.centerTitleStyles}>Signed in</div>
        </div>
      </AuthCard>
    );
  }

  if (viewState === "BLOCKED") {
    return (
      <AuthCard>
        <div className={Styles.centerCardStyles}>
          <div className={Styles.warnIconStyles}>
            <CircleAlertIcon size={24} />
          </div>
          <div className={Styles.titleStyles}>Verify your email first</div>
          <div className={Styles.centerSubtextStyles}>Taking you to the verification step.</div>
        </div>
      </AuthCard>
    );
  }

  if (viewState === "LIMITED") {
    return (
      <AuthCard>
        <div className={Styles.centerCardStyles}>
          <div className={Styles.warnIconStyles}>
            <CircleAlertIcon size={24} />
          </div>
          <div className={Styles.titleStyles}>Too many attempts</div>
          <div className={Styles.centerSubtextStyles}>
            This account is locked for 15 minutes after too many failed sign-ins.
          </div>
        </div>
      </AuthCard>
    );
  }

  if (viewState === "UNAVAILABLE") {
    return (
      <AuthCard>
        <div className={Styles.centerCardStyles}>
          <div className={Styles.warnIconStyles}>
            <CircleAlertIcon size={24} />
          </div>
          <div className={Styles.titleStyles}>Sign-in is temporarily unavailable</div>
          <div className={Styles.centerSubtextStyles}>Try again in a moment.</div>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      footer={
        <>
          New to Slashit?{" "}
          <Link to="/sign-up" className={Styles.footerLinkStyles}>
            Create an account
          </Link>
        </>
      }
    >
      <div className={Styles.titleStyles}>Sign in</div>

      {isError ? (
        <div className={Styles.errorBannerStyles}>
          <CircleAlertIcon size={16} className="mt-0.5 shrink-0" />
          <div>That email or password is not right.</div>
        </div>
      ) : null}

      <button
        type="button"
        onClick={handleGoogleSignIn}
        disabled={isLoading}
        className={Styles.googleButtonStyles}
      >
        <GoogleGMark />
        <span>Continue with Google</span>
      </button>

      <div className={Styles.dividerStyles}>
        <span className={Styles.dividerLineStyles} />
        <span>or</span>
        <span className={Styles.dividerLineStyles} />
      </div>

      <form onSubmit={handleSubmit}>
        <div className={Styles.formRowStyles}>
          <div className={Styles.fieldLabelRowStyles}>
            <span>Email</span>
          </div>
          <input
            type="email"
            autoComplete="email"
            required
            disabled={isLoading}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="jordan@example.com"
            className={Styles.inputStyles}
          />
        </div>

        <div className={Styles.formRowLastStyles}>
          <div className={Styles.fieldLabelRowStyles}>
            <span>Password</span>
            <Link to="/forgot-password" className={Styles.fieldLabelLinkStyles}>
              Forgot password?
            </Link>
          </div>
          <input
            type="password"
            autoComplete="current-password"
            required
            disabled={isLoading}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="••••••••••"
            className={Styles.inputStyles}
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
              <span>Signing in…</span>
            </>
          ) : (
            <span>Sign in</span>
          )}
        </Button>
      </form>
    </AuthCard>
  );
};

export default SignInController;
