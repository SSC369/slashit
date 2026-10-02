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
  "max-w-[560px] rounded-[10px] rounded-br-[3px] border border-border bg-card px-3.5 py-2.5 font-mono text-[13.5px] text-foreground wrap-anywhere";

export const cardStyles = "overflow-hidden rounded-lg border border-border bg-card";
export const cardHeadStyles = "flex items-center gap-2.5 border-b border-border px-4 py-3";
export const cardFootStyles =
  "flex items-center justify-between border-t border-border bg-card px-4 py-2.5 text-xs text-foreground-tertiary";

export const pillBaseStyles = "inline-flex min-w-0 max-w-full h-[23px] items-center gap-1.5 rounded-full border px-2.5 text-[11.5px] font-medium";
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
  "mt-3 rounded-lg border border-border bg-card px-3.5 py-2.5 font-mono text-[13.5px] text-foreground wrap-anywhere";
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
export const historySearchDetailStyles =
  "mt-1.5 flex items-center gap-2 text-[12.5px] text-foreground-secondary";
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

// Memory cards (004 design: MemorySaved, MemorySecretCaution, MemoriesLookup, CaptureStates)
export const memoryFieldsGridStyles = "grid grid-cols-[minmax(0,1fr)_170px] gap-px bg-border";
export const cautionInCardStyles = "mx-4 my-3 rounded-[9px]";
export const memoryListRowStyles =
  "flex cursor-pointer items-center justify-between gap-4 px-4 py-2.5 hover:bg-background";
export const memoryHintStyles = "px-4 py-3 text-[13px] text-foreground-secondary";

// Forget (004 design: ForgetPick, ForgetConfirm, ForgetAll, HistoryForgotten)
export const forgetPickRowStyles = "flex cursor-pointer items-center gap-3 border-t border-border px-4 py-3";
export const forgetPickRowOnStyles = "bg-accent-wash";
export const forgetRadioStyles = "h-4 w-4 shrink-0 accent-[var(--color-accent)]";
export const forgetConfirmCardStyles = "overflow-hidden rounded-lg border border-destructive-wash bg-card";
export const forgetConfirmBodyStyles = "flex gap-3.5 px-[18px] pb-3.5 pt-[18px]";
export const forgetConfirmIconStyles =
  "flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[9px] bg-destructive-wash text-destructive";
export const forgetConfirmTitleStyles = "text-base font-semibold text-foreground";
export const forgetConfirmTextStyles = "mt-1.5 text-[13.5px] text-foreground-secondary";
export const forgetConfirmBackupStyles = "mt-2.5 text-[12.5px] text-foreground-tertiary";
export const forgetActionsStyles = "flex justify-end gap-2.5 border-t border-border bg-background px-4 py-3";
export const forgetErrorStyles = "px-4 pb-3 text-[13px] text-destructive";

// Conflict (004 design: Main, MobileConflict). The pair is design delta `.pair`.
export const conflictLeadStyles = "px-4 pt-3 text-[13.5px] text-foreground-secondary";
export const conflictPairStyles = "grid grid-cols-1 gap-2.5 px-4 py-3 sm:grid-cols-2";
export const conflictSideStyles = "rounded-[10px] border border-border bg-background px-3.5 py-3";
export const conflictSideNewStyles = "border-accent bg-accent-wash";
export const conflictSideTextStyles = "mt-1 text-[14.5px] font-medium text-foreground";
export const conflictSideMetaStyles = "mt-1 text-xs text-foreground-tertiary";
export const conflictAnswerRowStyles =
  "flex cursor-pointer items-start gap-3 border-t border-border px-4 py-3 first:border-t-0";
export const conflictAnswerRowOnStyles = "bg-accent-wash";
export const conflictAnswerTitleStyles = "text-[14px] font-semibold text-foreground";
export const conflictAnswerBodyStyles = "mt-0.5 text-[13px] text-foreground-secondary";
export const conflictActionsStyles =
  "flex flex-col-reverse gap-2.5 border-t border-border bg-background px-4 py-3 sm:flex-row sm:justify-end";
export const conflictDeferredStyles = "flex items-center justify-between gap-3 px-4 py-3 text-[13px] text-foreground-secondary";
export const waitingPillRowStyles = "mb-2 flex justify-center";

// Search (005 design: Main, SearchPassport, SearchResults, SearchDegraded, SearchStates)
export const pillPendingStyles = "border-command-wash bg-command-wash text-command";
export const searchStripStyles =
  "flex items-center gap-2 border-b border-border bg-command-wash px-4 py-2.5 text-[12.5px] text-command";
export const searchGroupStyles = "pb-1.5";
export const searchGroupSeparatorStyles = "border-t border-border";
export const searchGroupHeadStyles = "flex items-center justify-between px-4 pb-1 pt-3";
export const searchGroupLabelStyles = "inline-flex items-center gap-2 text-[13px] font-semibold text-foreground";
export const searchGroupCountStyles = "text-xs text-foreground-tertiary";
export const searchHitRowStyles =
  "flex cursor-pointer items-center gap-3 px-4 py-2 hover:bg-background";
export const searchHitTitleStyles = "min-w-0 flex-1 truncate font-medium text-foreground";
export const searchHitDateStyles = "w-[140px] shrink-0 text-right text-[12.5px] text-foreground-tertiary";
export const searchHitStatusStyles = "flex w-[120px] shrink-0 justify-end";
export const searchNoMatchBodyStyles = "px-4 py-3.5 text-[13.5px] text-foreground-secondary";
// Design deltas `.answer`, `.alabel` and `.cite` (slice 2: Main, SearchNoSupport)
export const answerBlockStyles =
  "border-b border-border px-4 pb-[15px] pt-3.5 text-[14.5px] leading-[1.65] text-foreground";
export const answerLabelStyles =
  "mb-1.5 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.07em] text-accent";
export const answerNoSupportStyles = "text-foreground-tertiary";
export const answerCommandStyles = "font-mono text-foreground";
export const citeMarkerStyles =
  "ml-[3px] inline-flex h-[18px] min-w-[18px] cursor-pointer items-center justify-center rounded-[5px] border-0 bg-accent-wash px-1 align-[1px] font-mono text-[11px] font-semibold text-accent";
export const citeMarkerRowStyles = "ml-0 shrink-0";
export const typeDotTaskStyles = "h-1.5 w-1.5 shrink-0 rounded-sm bg-command";
export const typeDotReminderStyles = "h-1.5 w-1.5 shrink-0 rounded-full bg-accent";
export const typeDotMemoryStyles = "h-1.5 w-1.5 shrink-0 rounded-full bg-accent ring-2 ring-accent-wash";

// Event cards (007 design: Main, EventResolved, EventAsk, EventCaptureStates,
// EventsList, EventsListStates). `.monthhead`, `.evrow`, `.datebox`, `.evmeta`.
export const eventFieldsGridStyles = "grid grid-cols-2 gap-px bg-border";
export const pillRepeatStyles = "border-accent-wash bg-accent-wash text-accent";
export const monthHeadStyles =
  "flex items-center justify-between border-b border-t border-b-border-strong border-t-border bg-group-head px-4 py-[9px] text-[11px] font-semibold uppercase tracking-[0.07em] text-foreground-tertiary first:border-t-0";
export const monthCountStyles = "font-mono font-medium normal-case tracking-normal";
export const eventRowStyles =
  "grid cursor-pointer grid-cols-[76px_minmax(0,1fr)_210px_150px] items-center gap-3 border-b border-divider px-4 py-[11px] last:border-b-0 hover:bg-background";
export const dateBoxStyles =
  "flex h-[46px] w-[46px] flex-col items-center justify-center rounded-[9px] border border-border-strong bg-card leading-[1.1]";
export const dateBoxDayStyles = "text-[17px] font-semibold text-foreground";
export const dateBoxWeekdayStyles =
  "text-[10px] font-semibold uppercase tracking-[0.07em] text-foreground-tertiary";
export const eventTitleStyles = "truncate font-medium text-foreground";
export const eventMetaStyles = "mt-0.5 flex items-center gap-2.5 text-[12.5px] text-foreground-secondary";
export const eventMetaItemStyles = "inline-flex min-w-0 items-center gap-1 truncate";
export const eventMetaAlertStyles = "inline-flex shrink-0 items-center gap-1 text-accent";
export const eventWhenStyles = "text-[13px] text-foreground-secondary";
export const eventPillsStyles = "flex justify-end gap-1.5";
export const eventListHeadStyles =
  "text-[11px] font-semibold uppercase tracking-[0.07em] text-foreground-tertiary";
export const eventEmptyStyles = "flex flex-col items-center px-6 py-[34px] text-center";
export const eventEmptyIconStyles = "mb-2 text-foreground-tertiary";
export const eventEmptyTitleStyles = "font-medium text-foreground";
export const eventEmptyBodyStyles = "max-w-[380px] text-[13px] text-foreground-secondary";
export const eventSkeletonRowStyles = "flex items-center gap-3 border-b border-border px-4 py-[11px]";
export const eventChoiceRowStyles = "mt-3 flex flex-wrap gap-2";
