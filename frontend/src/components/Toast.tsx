import { Check, X } from "lucide-react";
import { useEffect, useRef, useState, type ReactElement } from "react";
import { Link } from "react-router";

import type { Toast as ToastModel } from "../stores/ToastStore";
import * as Styles from "./styles";

export const TOAST_LIFETIME_MS = 4000;

interface ToastProps {
  toast: ToastModel | null;
  onDismiss: (id: string) => void;
}

/**
 * The success toast (design §4): hides after four seconds, or on its close
 * button. Hover or focus pauses the timer and leaving resumes it with the
 * time that was left, so reading it never races the clock.
 */
export const Toast = (props: ToastProps): ReactElement | null => {
  const { toast, onDismiss } = props;
  const [isPaused, setIsPaused] = useState(false);
  const remainingMsRef = useRef(TOAST_LIFETIME_MS);
  const toastId = toast?.id ?? null;

  useEffect(() => {
    remainingMsRef.current = TOAST_LIFETIME_MS;
    setIsPaused(false);
  }, [toastId]);

  useEffect(() => {
    if (toastId === null || isPaused) return;
    const startedAt = Date.now();
    const timeoutId = window.setTimeout(() => onDismiss(toastId), remainingMsRef.current);
    return () => {
      window.clearTimeout(timeoutId);
      remainingMsRef.current -= Date.now() - startedAt;
    };
    // onDismiss is a store action, stable by construction (repo-rules §13.4).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [toastId, isPaused]);

  if (toast === null) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={Styles.toastStyles}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onFocus={() => setIsPaused(true)}
      onBlur={() => setIsPaused(false)}
    >
      <span className={Styles.toastCheckStyles}>
        <Check size={13} />
      </span>
      <span className={Styles.toastMessageStyles}>{toast.message}</span>
      <Link to={toast.linkTo} className={Styles.toastLinkStyles} onClick={() => onDismiss(toast.id)}>
        {toast.linkLabel}
      </Link>
      <button
        type="button"
        aria-label="Dismiss"
        className={Styles.toastCloseStyles}
        onClick={() => onDismiss(toast.id)}
      >
        <X size={15} />
      </button>
    </div>
  );
};

export default Toast;
