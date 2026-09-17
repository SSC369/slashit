// Styles for the Reset password screen (both steps), colocated per
// frontend/rules/repo-rules.md §12. Pixel-matched to
// process-docs/002-authentication/assets/canvas/ResetPassword.dc.html and
// 02-design.md §4. The six-box code input's own styles live in
// features/auth/components/styles.ts, shared with Verify email. Every colour
// is a tier-2 token from design-system/tokens.css; no raw hex here.

export const titleStyles =
  "m-0 mb-1.5 font-serif text-[26px] font-normal tracking-[-0.005em] text-foreground";

export const subtitleStyles =
  "m-0 mb-[22px] text-[13.5px] leading-normal text-foreground-secondary";

export const centerSubtitleStyles =
  "m-0 mb-[26px] text-center text-[13.5px] leading-normal text-foreground-secondary";

export const centerTitleStyles =
  "m-0 mb-1.5 text-center font-serif text-[26px] font-normal tracking-[-0.005em] text-foreground";

export const emailStyles = "font-mono";

// Error banner --------------------------------------------------------------

export const noteErrorStyles =
  "mb-[18px] flex gap-[11px] rounded-[10px] border border-destructive-wash bg-destructive-wash " +
  "px-[15px] py-[13px] text-[13px] leading-normal text-destructive";

export const noteErrorIconStyles = "mt-px shrink-0";

// Code step -----------------------------------------------------------------

export const resendRowStyles =
  "mb-[22px] mt-[18px] flex justify-center text-[12.5px] text-foreground-tertiary";

export const resendLinkStyles =
  "cursor-pointer border-0 bg-transparent p-0 font-sans text-[12.5px] text-accent " +
  "underline-offset-2 hover:underline disabled:cursor-not-allowed disabled:opacity-60";

// Password step -------------------------------------------------------------

export const formRowStyles = "mb-4 flex flex-col gap-1.5";

export const lastFormRowStyles = "mb-[22px] flex flex-col gap-1.5";

export const fieldLabelStyles = "text-[12.5px] font-medium text-foreground-secondary";

export const controlStyles =
  "h-[42px] w-full rounded-md border border-border-strong bg-card px-3.5 text-sm text-foreground " +
  "outline-none placeholder:text-foreground-tertiary focus:border-accent " +
  "focus:shadow-[0_0_0_3px_var(--color-accent-wash)] disabled:cursor-not-allowed disabled:opacity-60";

export const controlErrorStyles =
  "border-destructive shadow-[0_0_0_3px_var(--color-destructive-wash)]";

// Shared ---------------------------------------------------------------------

export const submitButtonStyles = "h-11 w-full justify-center gap-2 text-[14px]";

// Design §7: under prefers-reduced-motion the spinner is replaced by the
// static loading text alone, not a frozen spin.
export const spinnerStyles =
  "h-[15px] w-[15px] animate-spin rounded-full border-2 border-white/40 border-t-white " +
  "motion-reduce:hidden";

export const centerCardStyles = "text-center";

const iconCircleBaseStyles =
  "mx-auto mb-3.5 flex h-[52px] w-[52px] items-center justify-center rounded-full";

export const successIconStyles = `${iconCircleBaseStyles} bg-success-wash text-success`;

export const warnIconStyles = `${iconCircleBaseStyles} bg-command-wash text-command`;

export const statusBodyStyles = "text-[13.5px] leading-normal text-foreground-secondary";

export const footerLinkStyles = "text-accent hover:opacity-80";
