// Bell (design §6: bell with unread badge, on every topbar)
export const bellButtonStyles =
  "relative flex h-9 w-9 items-center justify-center rounded-md text-foreground-secondary hover:bg-card hover:text-foreground";
export const bellBadgeStyles =
  "absolute -right-0.5 -top-0.5 flex h-[17px] min-w-[17px] items-center justify-center rounded-full bg-destructive px-1 text-[10.5px] font-semibold text-white";

// Panel (NotificationPanel, NotificationStates): a 430 px slide-over
export const panelOverlayStyles = "fixed inset-0 z-30 bg-black/20";
export const panelStyles =
  "fixed inset-y-0 right-0 z-30 flex w-[430px] max-w-[calc(100vw-2.5rem)] flex-col border-l border-border bg-card shadow-2xl";
export const panelHeadStyles = "flex h-[60px] shrink-0 items-center gap-3 border-b border-border px-5";
export const panelTitleStyles = "text-[15px] font-semibold text-foreground";
export const panelUnreadStyles = "text-[12.5px] text-foreground-tertiary";
export const panelHeadActionsStyles = "ml-auto flex items-center gap-1";
export const panelLinkButtonStyles = "text-[12.5px] font-medium text-accent disabled:opacity-60";
export const panelCloseStyles =
  "flex h-8 w-8 items-center justify-center rounded-md text-foreground-secondary hover:bg-background hover:text-foreground";
export const panelBodyStyles = "flex-1 overflow-y-auto";
export const panelFootStyles =
  "shrink-0 border-t border-border bg-background px-5 py-3 text-[12px] text-foreground-tertiary";
export const panelStateStyles =
  "flex flex-col items-center justify-center px-8 py-16 text-center text-sm text-foreground-secondary";
export const panelStateTitleStyles = "text-[15px] font-semibold text-foreground";
export const panelStateBodyStyles = "mt-1.5 text-[13px] text-foreground-secondary";
export const panelSkeletonItemStyles = "flex flex-col gap-2 border-b border-border px-5 py-4";
export const panelLoadMoreStyles = "flex justify-center py-3";
export const inlineCommandStyles =
  "rounded border border-border-strong bg-background px-1 font-mono text-[12px] text-foreground";

// Item
export const itemStyles = "relative border-b border-border px-5 py-4 last:border-b-0";
export const itemUnreadStyles = "bg-accent-wash/40";
export const itemUnreadDotStyles = "absolute left-2 top-[22px] h-1.5 w-1.5 rounded-full bg-accent";
export const itemTitleRowStyles = "flex items-center gap-2";
export const itemTitleStyles = "text-[14px] font-medium text-foreground";
export const itemMetaStyles = "mt-1 text-[12.5px] text-foreground-tertiary";
export const itemActionsStyles = "mt-2.5 flex items-center gap-1.5";
export const itemErrorStyles = "mt-2 text-[12.5px] text-destructive";
export const markerBaseStyles =
  "inline-flex h-[20px] items-center rounded-full border px-2 text-[11px] font-medium";
export const markerLateStyles = "border-command-wash bg-command-wash text-command";
export const markerMissedStyles = "border-destructive-wash bg-destructive-wash text-destructive";
export const noticeStyles = "border-b border-border bg-command-wash px-5 py-3.5";

// Pop-up (ReminderToast): bottom-right, stays until acted on or closed, stacks
export const popupStackStyles =
  "pointer-events-none fixed bottom-5 right-7 z-40 flex w-[392px] max-w-[calc(100vw-2.5rem)] flex-col gap-3";
export const popupStyles =
  "pointer-events-auto rounded-xl border border-border-strong bg-card px-4 pb-3.5 pt-[15px] shadow-2xl";
export const popupHeadStyles = "mb-1.5 flex items-center gap-2 text-[12px] text-foreground-tertiary";
export const popupRepeatStyles =
  "inline-flex h-[20px] items-center rounded-full border border-accent-wash bg-accent-wash px-2 text-[11px] font-medium text-accent";
export const popupCloseStyles = "ml-auto flex text-foreground-tertiary hover:text-foreground";
export const popupTitleStyles = "text-[16px] font-semibold tracking-[-0.01em] text-foreground";
export const popupActionsStyles = "mt-3 flex items-center gap-2";
export const popupMessageStyles = "mt-2.5 text-[12.5px]";
export const popupErrorStyles = "text-destructive";
export const popupOfflineStyles = "text-command";

// Snooze menu
export const snoozeOptionStyles =
  "flex w-full items-center justify-between gap-6 px-3.5 py-2 text-left text-[13px] text-foreground hover:bg-background";
export const snoozeTimeStyles = "text-[12.5px] text-foreground-tertiary";
export const itemNoticeTitleRowStyles = "text-foreground-secondary";
export const itemNoticeTitleStyles = "text-foreground-secondary";
