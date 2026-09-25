// Records pane (shared by RecordsController / RecordDetailController)
export const paneStyles = "flex-1 overflow-y-auto px-10 py-7";

// Toolbar: tabs + search + sort
export const toolbarStyles = "mb-[18px] flex items-center justify-between";
export const tabsStyles = "flex gap-1.5";
export const tabStyles =
  "flex h-8 items-center rounded-md border border-transparent px-3.5 text-[13px] font-medium text-foreground-secondary";
export const tabOnStyles = "border-border-strong bg-card text-foreground";
export const tabHintStyles = "flex h-8 items-center px-2 text-[13px] italic text-foreground-tertiary";
export const toolbarRightStyles = "flex gap-2.5";
export const searchBoxStyles =
  "flex h-9 w-[280px] items-center gap-2.5 rounded-md border border-border-strong bg-card px-3 text-[13.5px] text-foreground-tertiary";
export const searchInputStyles = "w-full border-0 bg-transparent text-foreground outline-none placeholder:text-foreground-tertiary";

// Loading skeleton (table and detail page share the same pulse block)
export const skeletonBlockStyles = "h-[11px] animate-pulse rounded bg-border";

// Table
export const cardStyles = "overflow-hidden rounded-lg border border-border bg-card";
export const tableStyles = "w-full border-collapse bg-card";
export const theadRowStyles = "border-b border-border-strong bg-background";
export const thStyles = "px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-[0.07em] text-foreground-tertiary";
export const rowStyles = "cursor-pointer border-b border-border last:border-b-0 hover:bg-background";
export const tdStyles = "h-[52px] px-4 align-middle text-sm";
export const typeTagStyles = "inline-flex items-center gap-1.5 text-[12.5px] text-foreground-secondary";
export const typeDotStyles = "h-1.5 w-1.5 shrink-0 rounded-sm bg-command";
export const typeDotReminderStyles = "h-1.5 w-1.5 shrink-0 rounded-full bg-accent";
export const titleCellStyles = "font-medium text-foreground";
export const titleDoneCellStyles = "font-medium text-foreground-tertiary";
export const dateCellStyles = "text-foreground-secondary";
export const cardFootStyles =
  "flex items-center justify-between border-t border-border bg-background px-4 py-2.5 text-xs text-foreground-tertiary";

export const pillBaseStyles = "inline-flex h-[23px] items-center gap-1.5 rounded-full border px-2.5 text-[11.5px] font-medium";
export const pillPendingStyles = "border-command-wash bg-command-wash text-command";
export const pillDoneStyles = "border-success-wash bg-success-wash text-success";

// Empty state
export const emptyContainerStyles = "flex flex-1 flex-col items-center justify-center px-10 text-center";
export const emptyIconStyles =
  "mx-auto mb-[18px] flex h-[52px] w-[52px] items-center justify-center rounded-xl bg-background text-foreground-tertiary";
export const emptyTitleStyles = "text-[19px] font-semibold text-foreground";
export const emptyBodyStyles = "mt-2 max-w-[420px] text-sm text-foreground-secondary";
export const emptyActionStyles = "mt-5";

// Detail
export const breadcrumbStyles = "mb-5 flex items-center gap-2 text-[13px] text-foreground-tertiary";
export const breadcrumbCurrentStyles = "text-foreground";
export const detailTitleStyles = "font-serif text-[32px] leading-[1.2] text-foreground";
export const detailFieldsStyles = "mt-[22px]";
export const detailRowStyles = "flex border-b border-border py-3.5";
export const detailLabelStyles = "w-[150px] pt-0.5 text-[11px] font-semibold uppercase tracking-[0.07em] text-foreground-tertiary";
export const detailValueStyles = "flex-1 text-[14.5px] text-foreground";
export const detailInputBlockStyles = "mt-[22px]";
export const detailInputEchoStyles =
  "mt-2 rounded-lg border border-border bg-background px-3.5 py-3 font-mono text-[13.5px] text-foreground";
export const detailActionsRowStyles = "mt-[26px] flex gap-2.5";

// Edit form
export const formRowStyles = "mb-[18px] flex flex-col gap-1.5";
export const formLabelStyles = "text-[11px] font-semibold uppercase tracking-[0.07em] text-foreground-tertiary";
export const controlStyles =
  "flex h-[42px] items-center rounded-md border border-border-strong bg-card px-3.5 text-sm text-foreground";
export const controlInputStyles = "w-full border-0 bg-transparent text-[17px] text-foreground outline-none";
export const controlReadOnlyStyles = "text-foreground-secondary";
export const segStyles = "flex w-fit overflow-hidden rounded-md border border-border-strong";
export const segOptionStyles =
  "flex h-10 cursor-pointer items-center px-4 text-[13.5px] font-medium text-foreground-secondary";
export const segOptionOnStyles = "bg-accent text-white";
export const noteInfoStyles = "mt-1.5 flex gap-2.5 rounded-[10px] border border-accent-wash bg-accent-wash px-4 py-3.5";
export const noteInfoTextStyles = "text-[13.5px] text-foreground";
export const formActionsRowStyles = "mt-6 flex gap-2.5";

// Delete confirm modal
export const modalOverlayStyles = "fixed inset-0 z-10 flex items-center justify-center bg-black/30";
export const modalStyles = "w-[460px] overflow-hidden rounded-xl bg-card shadow-2xl";
export const modalBodyStyles = "flex gap-3 p-6 pb-5";
export const modalTitleStyles = "text-[17px] font-semibold text-foreground";
export const modalMessageStyles = "mt-1.5 text-[13.5px] text-foreground-secondary";
export const modalTaskNameStyles = "font-mono text-foreground";
export const modalErrorStyles =
  "mt-3 rounded-md border border-destructive-wash bg-destructive-wash px-3 py-2 text-[13px] text-destructive";
export const modalActionsStyles = "flex justify-end gap-2.5 border-t border-border bg-background px-6 py-3.5";

// Reminders tab (003 design: Main, RecordsLoading, RemindersOffline)
export const groupHeadCellStyles = "p-0";
export const groupHeadStyles =
  "flex items-center justify-between border-b border-border-strong bg-background px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.07em] text-foreground-tertiary";
export const groupCountStyles = "font-mono font-medium normal-case tracking-normal";
export const secondaryCellStyles = "whitespace-nowrap text-foreground-secondary";
export const showMoreCellStyles = "px-4 py-2.5 text-[13px] font-medium text-accent";
export const offlineNoteStyles =
  "mb-[18px] flex items-start gap-2.5 rounded-[10px] border border-command-wash bg-command-wash px-4 py-3 text-[13.5px] text-foreground";
export const offlineNoteTitleStyles = "font-semibold";

// Reminders tab notices: empty, error, no match, session ended
export const noticeCardStyles =
  "flex flex-col items-center rounded-lg border border-border bg-card px-10 py-14 text-center";
export const noticeExampleStyles =
  "mt-4 rounded-md border border-border bg-background px-3 py-1.5 font-mono text-[13px] text-foreground";

// Reminder edit form (003 design: ReminderEdit and its states)
export const formGridStyles = "grid grid-cols-2 gap-4";
export const controlErrorStyles = "border-destructive";
export const fieldErrorStyles = "text-[12.5px] text-destructive";
export const controlNativeInputStyles = "w-full border-0 bg-transparent text-sm text-foreground outline-none";
export const intervalRowStyles = "flex items-center gap-2.5";
export const intervalInputStyles =
  "h-[42px] w-20 rounded-md border border-border-strong bg-card px-3 text-sm text-foreground outline-none";
export const chipsStyles = "flex flex-wrap gap-1.5";
export const chipStyles =
  "flex h-[34px] min-w-[38px] items-center justify-center rounded-md border border-border-strong bg-card px-2.5 text-[13px] font-medium text-foreground-secondary disabled:opacity-60";
export const chipOnStyles = "border-accent bg-accent text-white";
export const bannerErrorStyles =
  "mb-5 flex gap-2.5 rounded-[10px] border border-destructive-wash bg-destructive-wash px-4 py-3.5";
export const bannerWarnStyles =
  "mb-5 flex gap-2.5 rounded-[10px] border border-command-wash bg-command-wash px-4 py-3.5";
export const bannerTitleStyles = "text-[14.5px] font-semibold text-foreground";
export const bannerBodyStyles = "mt-0.5 text-[13.5px] text-foreground-secondary";

// Reminder detail (003 design: ReminderDetail, ReminderDetailLoading, ReminderNotFound)
export const detailHeadStyles = "flex items-start justify-between gap-4";
export const detailPillsStyles = "mt-2.5 flex flex-wrap gap-2";
export const pillRepeatStyles = "border-accent-wash bg-accent-wash text-accent";
export const detailSubValueStyles = "mt-0.5 text-[12.5px] text-foreground-tertiary";
export const detailMetaStyles = "mt-[22px] text-[12.5px] text-foreground-tertiary";
export const detailActionsInlineStyles = "flex shrink-0 gap-2.5";

// Done and Snooze on a Needs attention row (Main)
export const rowActionsStyles = "ml-2.5 inline-flex items-center gap-1.5 align-middle";
export const rowActionErrorStyles = "text-[12px] text-destructive";

// Memories (004 design: RecordsMemories, RecordsAll, MemoryDetail, MemoryEdit, MemoriesStates)
export const typeDotMemoryStyles = "h-1.5 w-1.5 shrink-0 rounded-full bg-accent ring-2 ring-accent-wash";
export const categoryChipsRowStyles = "-mt-1 mb-4 flex flex-wrap items-center gap-1.5";
export const categoryChipStyles =
  "flex h-7 items-center rounded-full border border-border-strong bg-card px-3 text-[12.5px] font-medium text-foreground-secondary";
export const categoryChipOnStyles = "border-foreground bg-foreground text-background";
export const memoryTextCellStyles = "font-medium text-foreground";
export const textareaStyles =
  "min-h-[92px] w-full resize-y rounded-md border border-border-strong bg-card px-3.5 py-3 text-sm leading-[1.45] text-foreground outline-none";
export const counterStyles = "mt-1 text-right text-[11.5px] text-foreground-tertiary";
export const counterOverStyles = "text-destructive";
export const formHintStyles = "text-[12.5px] text-foreground-tertiary";
