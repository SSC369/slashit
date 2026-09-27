// Styles for the Sign In screen, colocated per frontend/rules/repo-rules.md
// §12. Pixel-matched to
// process-docs/002-authentication/assets/canvas/SignIn.dc.html. Every colour
// comes from a tier-2 token in design-system/tokens.css; no raw hex here
// (the Google "G" mark in SignInController.tsx is the one deliberate
// exception, called out where it is defined).

export const titleStyles =
  "mb-[22px] font-serif text-[26px] font-normal tracking-[-0.005em] text-foreground";

export const centerCardStyles = "text-center";

export const centerTitleStyles =
  "mb-0 font-serif text-[26px] font-normal tracking-[-0.005em] text-foreground";

export const centerSubtextStyles = "text-[13.5px] text-foreground-secondary";

const iconCircleBaseStyles =
  "mx-auto mb-3.5 flex h-[52px] w-[52px] items-center justify-center rounded-full";

export const successIconStyles = `${iconCircleBaseStyles} bg-success-wash text-success`;

export const warnIconStyles = `${iconCircleBaseStyles} bg-command-wash text-command`;

export const errorBannerStyles =
  "mb-[18px] flex items-start gap-2.5 rounded-[10px] border border-destructive-wash " +
  "bg-destructive-wash px-4 py-3.5 text-[13px] leading-relaxed text-destructive";

/** 002 FR-23: neutral, not the red banner. The user did nothing wrong. */
export const infoNoteStyles =
  "mb-[18px] flex items-start gap-2.5 rounded-[10px] border border-border-strong " +
  "bg-card px-4 py-3.5 text-[13px] leading-relaxed text-foreground-secondary";

export const googleButtonStyles =
  "mb-[18px] flex h-11 w-full items-center justify-center gap-2.5 rounded-md border " +
  "border-border-strong bg-card text-sm font-medium text-foreground " +
  "disabled:cursor-not-allowed disabled:opacity-60";

export const dividerStyles = "mb-[18px] flex items-center gap-3 text-xs text-foreground-tertiary";

export const dividerLineStyles = "h-px flex-1 bg-border";

export const formRowStyles = "mb-4 flex flex-col gap-1.5";

export const formRowLastStyles = "mb-[22px] flex flex-col gap-1.5";

export const fieldLabelRowStyles =
  "flex items-center justify-between text-[12.5px] font-medium text-foreground-secondary";

export const fieldLabelLinkStyles = "font-medium text-accent hover:opacity-80";

export const inputStyles =
  "h-[42px] w-full rounded-md border border-border-strong bg-card px-3.5 text-sm " +
  "text-foreground outline-none placeholder:text-foreground-tertiary focus:border-accent " +
  "disabled:cursor-not-allowed disabled:opacity-60";

export const submitButtonStyles = "h-11 w-full justify-center gap-2 text-sm";

export const spinnerStyles =
  "h-[15px] w-[15px] animate-spin rounded-full border-2 border-white/40 border-t-white";

export const footerLinkStyles = "text-accent hover:opacity-80";
