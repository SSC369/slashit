import { AlertCircle, Check } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useRef, useState, type ReactElement } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";

import { supabaseClient } from "../../../../api/lib/supabaseClient";
import Button from "../../../../design-system/components/Button";
import AuthCard from "../../components/AuthCard";
import OtpInput from "../../components/OtpInput";
import * as Styles from "./styles";

const OTP_LENGTH = 6;
const RESEND_COOLDOWN_SECONDS = 30;
const SUCCESS_REDIRECT_DELAY_MS = 750;
const RATE_LIMIT_STATUS = 429;
const RATE_LIMIT_CODE = "over_request_rate_limit";
const EXPIRED_CODE = "otp_expired";

type StageType = "FORM" | "LOADING" | "SUCCESS" | "LIMITED";
type ErrorKindType = "NONE" | "WRONG" | "EXPIRED";

interface LocationState {
  email?: string;
}

const formatCooldown = (seconds: number): string => `0:${String(seconds).padStart(2, "0")}`;

const VerifyEmailController = (): ReactElement => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();

  const emailFromQuery = searchParams.get("email");
  const emailFromState = (location.state as LocationState | null)?.email ?? null;
  const email = emailFromQuery ?? emailFromState ?? null;
  const hasEmail = email !== null;

  const [code, setCode] = useState("");
  const [stage, setStage] = useState<StageType>("FORM");
  const [errorKind, setErrorKind] = useState<ErrorKindType>("NONE");
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
    const isSuccess = stage === "SUCCESS";
    if (!isSuccess) return;
    const timeoutId = setTimeout(() => {
      navigate("/", { replace: true });
    }, SUCCESS_REDIRECT_DELAY_MS);
    return () => clearTimeout(timeoutId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  const handleVerify = async (submittedCode: string): Promise<void> => {
    const isSubmittable = hasEmail && submittedCode.length === OTP_LENGTH && email !== null;
    if (!isSubmittable) return;

    setStage("LOADING");
    const { error } = await supabaseClient.auth.verifyOtp({
      email,
      token: submittedCode,
      type: "signup",
    });

    const isStillCurrentSubmission = codeRef.current === submittedCode;
    if (!isStillCurrentSubmission) return;

    if (!error) {
      setStage("SUCCESS");
      return;
    }

    const isRateLimited = error.status === RATE_LIMIT_STATUS || error.code === RATE_LIMIT_CODE;
    if (isRateLimited) {
      setStage("LIMITED");
      return;
    }

    const isExpired = error.code === EXPIRED_CODE;
    setErrorKind(isExpired ? "EXPIRED" : "WRONG");
    if (isExpired) setCooldownSeconds(0);
    setStage("FORM");
  };

  const handleChange = (value: string): void => {
    setCode(value);
    const isComplete = value.length === OTP_LENGTH;
    if (isComplete) void handleVerify(value);
  };

  const handleVerifyClick = (): void => {
    void handleVerify(code);
  };

  const handleResend = async (): Promise<void> => {
    if (!hasEmail || email === null) return;
    setErrorKind("NONE");
    setCode("");
    setCooldownSeconds(RESEND_COOLDOWN_SECONDS);
    await supabaseClient.auth.resend({ type: "signup", email });
  };

  const isLoading = stage === "LOADING";
  const hasError = errorKind !== "NONE";
  const isResendAvailable = errorKind === "EXPIRED" || cooldownSeconds <= 0;
  const isVerifyDisabled = !hasEmail || code.length !== OTP_LENGTH || isLoading;
  const isResendDisabled = !hasEmail || !isResendAvailable;
  const subtitle =
    email !== null ? (
      <>
        We sent a 6-digit code to <span className={Styles.emailStyles}>{email}</span>
      </>
    ) : (
      "We sent a 6-digit code to your email."
    );

  if (stage === "SUCCESS") {
    return (
      <AuthCard>
        <div className={Styles.centerMsgStyles}>
          <div className={Styles.checkCircleStyles}>
            <Check size={24} />
          </div>
          <div className={Styles.titleStyles}>Email verified</div>
          <div className={Styles.confirmSubtitleStyles}>Taking you into Slashit now.</div>
        </div>
      </AuthCard>
    );
  }

  if (stage === "LIMITED") {
    return (
      <AuthCard>
        <div className={Styles.centerMsgStyles}>
          <div className={Styles.amberWarnStyles}>
            <AlertCircle size={24} />
          </div>
          <div className={Styles.titleStyles}>Too many attempts</div>
          <div className={Styles.confirmSubtitleStyles}>
            This code is now blocked. Request a new one in 15 minutes.
          </div>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      footer={
        <>
          Wrong email? <Link to="/sign-up" className={Styles.footerLinkStyles}>Start over</Link>
        </>
      }
    >
      <div className={Styles.titleStyles}>Verify your email</div>
      <div className={Styles.subtitleStyles}>{subtitle}</div>

      {hasError && (
        <div className={Styles.noteErrorStyles}>
          <AlertCircle size={16} className={Styles.noteIconStyles} />
          <div>
            {errorKind === "EXPIRED"
              ? "This code expired. Request a new one below."
              : "That code is not right. Check it and try again."}
          </div>
        </div>
      )}

      <OtpInput
        value={code}
        onChange={handleChange}
        error={hasError}
        disabled={isLoading}
        autoFocus
      />

      <div className={Styles.resendRowStyles} aria-live="polite">
        {isResendAvailable ? (
          <button
            type="button"
            className={Styles.resendLinkStyles}
            disabled={isResendDisabled}
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
        className={Styles.verifyButtonStyles}
        disabled={isVerifyDisabled}
        onClick={handleVerifyClick}
      >
        {isLoading ? (
          <>
            <span className={Styles.spinnerStyles} />
            <span>Verifying&hellip;</span>
          </>
        ) : (
          <span>Verify</span>
        )}
      </Button>
    </AuthCard>
  );
};

export default observer(VerifyEmailController);
