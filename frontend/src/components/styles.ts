export const bannerBaseStyles =
  "flex shrink-0 items-center gap-3 border-b border-border px-5 py-2.5 text-[13px]";
export const offlineBannerStyles = "border-command-wash bg-command-wash text-foreground";
export const updateBannerStyles = "border-accent-wash bg-accent-wash text-foreground";
export const bannerTextStyles = "flex-1";
export const bannerActionsStyles = "flex items-center gap-2";

export const installPromptStyles =
  "fixed bottom-5 left-1/2 z-50 flex w-[360px] max-w-[calc(100vw-2.5rem)] -translate-x-1/2 items-start gap-3 rounded-lg border border-border-strong bg-card px-4 py-3.5 shadow-lg";
export const installPromptTitleStyles = "text-[13.5px] font-semibold text-foreground";
export const installPromptBodyStyles = "mt-0.5 text-[12.5px] text-foreground-secondary";
export const installPromptActionsStyles = "mt-3 flex gap-2";

export const inlineSpinnerStyles = "inline-block animate-spin rounded-full border-2 border-current border-t-transparent text-accent";

// Skeleton bar (design §7: shimmer stops under reduced motion, leaving a still bar)
export const skeletonStyles = "block h-[11px] animate-pulse rounded bg-border motion-reduce:animate-none";

// Busy button (design §6): a spinner alone replaces the label; the hidden
// label keeps the button's width so nothing shifts.
export const busyButtonStyles = "relative disabled:cursor-progress disabled:opacity-100";
export const busyButtonLabelStyles = "inline-flex items-center gap-1.5";
export const busyButtonSpinnerWrapStyles = "absolute inset-0 flex items-center justify-center";
export const busyButtonSpinnerStyles =
  "h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent motion-reduce:animate-none";

// Success toast (design §4): top-centre, 16 px under the header, on the ink
// ground so it inverts in dark with no new token.
export const toastStyles =
  "absolute left-1/2 top-[76px] z-30 flex max-w-[calc(100%-2rem)] -translate-x-1/2 items-center gap-3 rounded-lg bg-foreground py-2.5 pl-3.5 pr-3 text-sm text-background shadow-lg";
export const toastCheckStyles =
  "flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-full bg-success text-white";
export const toastMessageStyles = "min-w-0 truncate";
export const toastLinkStyles = "shrink-0 font-medium underline underline-offset-2";
export const toastCloseStyles = "ml-1 flex shrink-0 opacity-70 hover:opacity-100";

// Reminder status pill (design §8: Upcoming · Fired, not done · Missed · Done)
export const statusPillBaseStyles =
  "inline-flex h-[23px] items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 text-[11.5px] font-medium";
export const statusPillUpcomingStyles = "border-command-wash bg-command-wash text-command";
export const statusPillFiredStyles = "border-accent-wash bg-accent-wash text-accent";
export const statusPillMissedStyles = "border-destructive-wash bg-destructive-wash text-destructive";
export const statusPillDoneStyles = "border-success-wash bg-success-wash text-success";

// Page topbar: the title and the bell, on every page (003 slice 2)
export const pageTopbarStyles =
  "flex h-[60px] shrink-0 items-center justify-between border-b border-border bg-background px-7";
export const pageTopbarTitleStyles = "text-[17px] font-semibold tracking-[-0.01em] text-foreground";
export const pageTopbarActionsStyles = "flex items-center gap-1.5";
