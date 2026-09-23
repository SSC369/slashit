// Empty state
export const emptyContainerStyles = "flex flex-1 flex-col items-center justify-center px-10";
export const emptyColumnStyles = "w-full max-w-[760px] text-center";
export const emptyHeadlineStyles = "font-serif text-[40px] leading-[1.15] tracking-[-0.01em] text-foreground";
export const emptySubheadStyles = "mt-3 text-[15px] text-foreground-secondary";
export const emptySuggestionsRowStyles = "mt-6 flex justify-center gap-2";

// Turn stream
export const streamContainerStyles = "flex flex-1 flex-col gap-5 overflow-y-auto px-10 pb-2 pt-8";
export const streamColumnStyles = "mx-auto flex w-full max-w-[760px] flex-col gap-[22px]";

export const turnStyles = "flex flex-col gap-2.5";
export const saidRowStyles = "flex justify-end";
export const saidBoxStyles =
  "max-w-[560px] rounded-[10px] rounded-br-[3px] border border-border bg-card px-3.5 py-2.5 font-mono text-[13.5px] text-foreground";

export const cardStyles = "overflow-hidden rounded-lg border border-border bg-card";
export const cardHeadStyles = "flex items-center gap-2.5 border-b border-border px-4 py-3";
export const cardFootStyles =
  "flex items-center justify-between border-t border-border bg-card px-4 py-2.5 text-xs text-foreground-tertiary";

export const pillBaseStyles = "inline-flex h-[23px] items-center gap-1.5 rounded-full border px-2.5 text-[11.5px] font-medium";
export const pillWaitStyles = "border-accent-wash bg-accent-wash text-accent";
export const pillDoneStyles = "border-success-wash bg-success-wash text-success";
export const pillMutedStyles = "border-border-strong bg-background text-foreground-tertiary";
export const pillErrStyles = "border-destructive-wash bg-destructive-wash text-destructive";

export const fieldsGridStyles = "grid grid-cols-3 gap-px bg-border";
export const fieldCellStyles = "flex flex-col gap-1 bg-card px-4 py-3.5";
export const fieldLabelStyles = "text-[11px] font-semibold uppercase tracking-[0.07em] text-foreground-tertiary";
export const fieldValueStyles = "text-[14.5px] font-medium text-foreground";

export const taskListRowStyles = "flex justify-between px-4 py-2.5";
export const taskListDueStyles = "text-[13px] text-foreground-tertiary";

export const pendingCardStyles = "overflow-hidden rounded-lg border border-accent-wash bg-card";
export const pendingHeadStyles = "flex items-center gap-2.5 bg-accent-wash px-4 py-3";
export const pendingBodyStyles = "px-4 py-4";
export const pendingQuestionStyles = "text-[15px] font-medium text-foreground";
export const pendingHintStyles = "mt-1.5 text-[13px] text-foreground-secondary";
export const pendingAnswerRowStyles = "mt-3.5 flex gap-2.5";
export const pendingAnswerFieldStyles =
  "flex h-[38px] flex-1 items-center rounded-md border border-border-strong bg-card px-3";
export const pendingAnswerInputStyles = "w-full border-0 bg-transparent text-[13.5px] text-foreground outline-none";

export const noteBaseStyles = "flex items-start gap-2.5 rounded-[10px] border px-4 py-3.5";
export const noteWarnStyles = "border-command-wash bg-command-wash";
export const noteErrStyles = "border-destructive-wash bg-destructive-wash";
export const noteTitleStyles = "text-[14.5px] font-semibold text-foreground";
export const noteBodyStyles = "mt-1 text-[13.5px] text-foreground-secondary";
export const noteInputEchoStyles =
  "mt-3 rounded-lg border border-border bg-card px-3.5 py-2.5 font-mono text-[13.5px] text-foreground";
export const noteActionsRowStyles = "mt-3 flex items-center gap-2";

// Command palette
export const paletteStyles =
  "absolute bottom-[70px] left-0 right-0 overflow-hidden rounded-lg border border-border-strong bg-card shadow-lg";
export const paletteTopStyles = "flex items-center justify-between border-b border-border px-3.5 py-2.5";
export const paletteFootStyles = "flex gap-4 border-t border-border bg-card px-3.5 py-2 text-[11.5px] text-foreground-tertiary";
export const commandRowStyles = "flex cursor-default items-center gap-3.5 border-b border-border px-3.5 py-2.5 last:border-b-0";
export const commandRowSelectedStyles = "bg-accent-wash";
export const commandNameStyles = "w-[158px] shrink-0 font-mono text-[13.5px] font-medium text-foreground";

// Command input bar
export const dockStyles = "relative shrink-0 px-10 pb-6 pt-3.5";
export const inputWrapStyles = "relative mx-auto max-w-[760px]";
export const inputBarStyles =
  "flex h-14 items-center gap-3 rounded-lg border border-border-strong bg-card px-4 shadow-sm focus-within:border-accent focus-within:ring-4 focus-within:ring-accent-wash";
export const slashBadgeStyles =
  "flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-md bg-command-wash text-sm font-medium text-command";
export const rawInputStyles = "min-w-0 flex-1 border-0 bg-transparent p-0 font-mono text-[15px] text-foreground outline-none";
export const kbdStyles = "rounded border border-border-strong bg-card px-1.5 py-0.5 font-mono text-[11px] text-foreground-secondary";
export const hintRowStyles = "mt-3 flex items-center justify-center gap-4 text-xs text-foreground-tertiary";

// History panel
export const historyOverlayStyles = "fixed inset-0 z-20 bg-black/30";
export const historyPanelStyles =
  "fixed inset-y-0 right-0 z-20 flex w-[420px] max-w-[calc(100vw-2.5rem)] flex-col border-l border-border bg-card shadow-2xl";
export const historyHeadStyles =
  "flex h-[60px] shrink-0 items-center justify-between border-b border-border px-5";
export const historyTitleStyles = "text-[15px] font-semibold text-foreground";
export const historyCloseStyles =
  "flex h-8 w-8 items-center justify-center rounded-md text-foreground-secondary hover:bg-background hover:text-foreground";
export const historyBodyStyles = "flex-1 overflow-y-auto px-5 py-4";
export const historyRowStyles = "border-b border-border py-3.5 last:border-b-0";
export const historyRowHeadStyles = "flex items-center justify-between gap-2.5";
export const historyInputTextStyles = "font-mono text-[13px] text-foreground";
export const historyTimeStyles = "shrink-0 text-[11.5px] text-foreground-tertiary";
export const historyDetailStyles = "mt-1.5 text-[12.5px] text-foreground-secondary";
export const historySkeletonRowStyles = "border-b border-border py-3.5 last:border-b-0";
export const historyEmptyStyles =
  "flex flex-1 flex-col items-center justify-center px-6 text-center text-sm text-foreground-tertiary";
export const historyErrorStyles =
  "flex flex-1 flex-col items-center justify-center gap-2.5 px-6 text-center text-sm text-foreground-secondary";
export const historyLoadMoreStyles = "mt-1 flex justify-center pb-1";

// Reminder cards (003 design: RemindCapture, RemindResolved, RemindList, RemindAsk)
export const fieldSubStyles = "text-[12.5px] text-foreground-tertiary";
export const fieldNoteStyles = "text-[12.5px] text-command";
export const cardFootActionsStyles = "flex items-center gap-2";
export const reminderListHeadStyles = "text-[13px] font-medium text-foreground";
export const reminderListRowStyles =
  "grid cursor-pointer grid-cols-[minmax(0,1fr)_170px_170px_120px] items-center gap-3 border-b border-border px-4 py-2.5 text-[13.5px] last:border-b-0 hover:bg-background";
export const reminderListNameStyles = "truncate font-medium text-foreground";
export const reminderListMetaStyles = "truncate text-foreground-secondary";
export const quickAnswerRowStyles = "mt-3 flex flex-wrap gap-2";
export const footLinkStyles = "text-accent hover:underline";
