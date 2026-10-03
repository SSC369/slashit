export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** Date (isoformat) */
  Date: { input: string; output: string; }
  /** Date with time (isoformat) */
  DateTime: { input: string; output: string; }
  /** An amount in whole paise, as a decimal string. */
  Paise: { input: string; output: string; }
};

export type AccountLocked = {
  __typename?: 'AccountLocked';
  message: Scalars['String']['output'];
  retryAfter?: Maybe<Scalars['DateTime']['output']>;
};

export type AccountNotVerified = {
  __typename?: 'AccountNotVerified';
  message: Scalars['String']['output'];
};

export type AlertNotSetReason =
  | 'CAP'
  | 'PASSED';

export type AnswerSentence = {
  __typename?: 'AnswerSentence';
  citations: Array<Scalars['Int']['output']>;
  text: Scalars['String']['output'];
};

export type AuthProviderUnavailable = {
  __typename?: 'AuthProviderUnavailable';
  message: Scalars['String']['output'];
};

export type CaptureHistoryPage = {
  __typename?: 'CaptureHistoryPage';
  items: Array<CaptureTurn>;
  nextCursor?: Maybe<Scalars['String']['output']>;
};

export type CaptureResult = EventCreated | EventLimitReached | EventsListed | ExpenseQuestionAsked | ExpenseRefused | ExpenseSaved | ExpenseSummary | MalformedResult | MemoriesListed | MemoryConflictAsked | MemorySaved | MemoryTooLong | NonCommandGuidance | PendingQuestionCreated | ProviderTimeout | ProviderUnavailable | ReminderCreated | ReminderLimitReached | RemindersListed | SearchResults | SearchTooLong | SharedQuotaExhausted | TaskCreated | TasksListed | UnrecognisedCommand | UserLimitReached;

export type CaptureTurn = {
  __typename?: 'CaptureTurn';
  affectedCount?: Maybe<Scalars['Int']['output']>;
  answerText?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  forgotten: Scalars['Boolean']['output'];
  id: Scalars['ID']['output'];
  inputText: Scalars['String']['output'];
  outcome: CaptureTurnOutcome;
  questionText?: Maybe<Scalars['String']['output']>;
  resultingEventId?: Maybe<Scalars['ID']['output']>;
  resultingExpenseId?: Maybe<Scalars['ID']['output']>;
  resultingMemoryId?: Maybe<Scalars['ID']['output']>;
  resultingPendingCaptureId?: Maybe<Scalars['ID']['output']>;
  resultingReminderId?: Maybe<Scalars['ID']['output']>;
  resultingTaskId?: Maybe<Scalars['ID']['output']>;
};

export type CaptureTurnOutcome =
  | 'DISCARDED'
  | 'EVENTS_LISTED'
  | 'EVENT_CREATED'
  | 'EXPENSES_SUMMARISED'
  | 'EXPENSE_SAVED'
  | 'MEMORY_CONFLICT_RESOLVED'
  | 'MEMORY_FORGOTTEN'
  | 'MEMORY_LISTED'
  | 'MEMORY_SAVED'
  | 'QUESTION_ASKED'
  | 'REFUSED'
  | 'REMINDER_CREATED'
  | 'SEARCHED'
  | 'TASK_CREATED';

export type ConflictAnswer =
  | 'BOTH'
  | 'KEEP_NEW'
  | 'KEEP_OLD';

export type DeleteEventResult = EventDeleted | EventNotFound;

export type DeleteExpenseResult = ExpenseDeleted | ExpenseNotFound;

export type DeleteReminderResult = ReminderDeleteSucceeded | ReminderNotFound;

export type Event = {
  __typename?: 'Event';
  /** How the alerts were read, as a lead named twice. Only on create. */
  alertNotes: Array<Scalars['String']['output']>;
  /** Every alert, soonest-firing first. */
  alerts: Array<EventAlert>;
  allDay: Scalars['Boolean']['output'];
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  endDate?: Maybe<Scalars['Date']['output']>;
  endTime?: Maybe<Scalars['String']['output']>;
  endsAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  location?: Maybe<Scalars['String']['output']>;
  occurrenceDate: Scalars['Date']['output'];
  occurrenceEndDate: Scalars['Date']['output'];
  origin: Scalars['String']['output'];
  originalInput?: Maybe<Scalars['String']['output']>;
  repeatYearly: Scalars['Boolean']['output'];
  scheduleTimezone: Scalars['String']['output'];
  startDate: Scalars['Date']['output'];
  startTime?: Maybe<Scalars['String']['output']>;
  startsAt: Scalars['DateTime']['output'];
  status: EventStatusType;
  title: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
  /** Why the schedule reads as it does. Only on create. */
  whenNotes: Array<Scalars['String']['output']>;
  whenText: Scalars['String']['output'];
};

export type EventAlert = {
  __typename?: 'EventAlert';
  firesAt: Scalars['DateTime']['output'];
  leadMinutes: Scalars['Int']['output'];
  text: Scalars['String']['output'];
};

export type EventAlertNotSet = {
  __typename?: 'EventAlertNotSet';
  leadMinutes: Scalars['Int']['output'];
  reason: AlertNotSetReason;
  text: Scalars['String']['output'];
};

export type EventCreated = {
  __typename?: 'EventCreated';
  alertsNotSet: Array<EventAlertNotSet>;
  event: Event;
};

export type EventDeleted = {
  __typename?: 'EventDeleted';
  id: Scalars['ID']['output'];
};

export type EventField =
  | 'DATE'
  | 'DESCRIPTION'
  | 'END'
  | 'LOCATION'
  | 'TITLE';

export type EventInput = {
  alertLeadsMinutes: Array<Scalars['Int']['input']>;
  description?: InputMaybe<Scalars['String']['input']>;
  endDate?: InputMaybe<Scalars['Date']['input']>;
  endTime?: InputMaybe<Scalars['String']['input']>;
  location?: InputMaybe<Scalars['String']['input']>;
  repeatYearly: Scalars['Boolean']['input'];
  startDate: Scalars['Date']['input'];
  startTime?: InputMaybe<Scalars['String']['input']>;
  title: Scalars['String']['input'];
};

export type EventInvalid = {
  __typename?: 'EventInvalid';
  field: EventField;
  message: Scalars['String']['output'];
  reason: EventInvalidReason;
};

export type EventInvalidReason =
  | 'EMPTY'
  | 'END_BEFORE_START'
  | 'LIMIT'
  | 'TOO_LONG';

export type EventLimitReached = {
  __typename?: 'EventLimitReached';
  limit: Scalars['Int']['output'];
  message: Scalars['String']['output'];
};

export type EventNotFound = {
  __typename?: 'EventNotFound';
  message: Scalars['String']['output'];
};

export type EventResult = Event | EventNotFound;

export type EventScope =
  | 'ALL'
  | 'UPCOMING';

export type EventStatusType =
  | 'HAPPENING_NOW'
  | 'PAST'
  | 'UPCOMING';

export type EventUpdated = {
  __typename?: 'EventUpdated';
  alertsNotSet: Array<EventAlertNotSet>;
  event: Event;
};

export type EventsListed = {
  __typename?: 'EventsListed';
  events: Array<Event>;
};

export type Expense = {
  __typename?: 'Expense';
  amountPaise: Scalars['Paise']['output'];
  category: ExpenseCategory;
  createdAt: Scalars['DateTime']['output'];
  description: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  origin: Scalars['String']['output'];
  originalInput: Scalars['String']['output'];
  spentOn: Scalars['Date']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type ExpenseCategory =
  | 'BILLS'
  | 'ENTERTAINMENT'
  | 'FOOD'
  | 'HEALTH'
  | 'OTHER'
  | 'SHOPPING'
  | 'TRANSPORT'
  | 'TRAVEL';

export type ExpenseCategoryTotal = {
  __typename?: 'ExpenseCategoryTotal';
  category: ExpenseCategory;
  totalPaise: Scalars['Paise']['output'];
};

export type ExpenseDeleted = {
  __typename?: 'ExpenseDeleted';
  id: Scalars['ID']['output'];
};

export type ExpenseField =
  | 'AMOUNT'
  | 'DESCRIPTION';

export type ExpenseInvalid = {
  __typename?: 'ExpenseInvalid';
  field: ExpenseField;
  length?: Maybe<Scalars['Int']['output']>;
  message: Scalars['String']['output'];
  reason: ExpenseInvalidReason;
};

export type ExpenseInvalidReason =
  | 'EMPTY'
  | 'NOT_POSITIVE'
  | 'TOO_LARGE'
  | 'TOO_LONG';

export type ExpenseNotFound = {
  __typename?: 'ExpenseNotFound';
  message: Scalars['String']['output'];
};

export type ExpensePeriod = {
  __typename?: 'ExpensePeriod';
  end?: Maybe<Scalars['Date']['output']>;
  key: ExpensePeriodKey;
  label: Scalars['String']['output'];
  phrase: Scalars['String']['output'];
  start?: Maybe<Scalars['Date']['output']>;
};

export type ExpensePeriodKey =
  | 'ALL_TIME'
  | 'LAST_MONTH'
  | 'LAST_WEEK'
  | 'MONTH'
  | 'THIS_MONTH'
  | 'THIS_WEEK'
  | 'THIS_YEAR'
  | 'TODAY';

export type ExpenseQuestionAsked = {
  __typename?: 'ExpenseQuestionAsked';
  amountCandidates: Array<Scalars['Paise']['output']>;
  kind: ExpenseQuestionKind;
  pendingCaptureId: Scalars['ID']['output'];
  question: Scalars['String']['output'];
  readDate?: Maybe<Scalars['Date']['output']>;
};

export type ExpenseQuestionKind =
  | 'AMOUNT'
  | 'AMOUNT_CHOICE'
  | 'DATE'
  | 'DESCRIPTION';

export type ExpenseRefusalReason =
  | 'AMOUNT_TOO_LARGE'
  | 'DESCRIPTION_TOO_LONG'
  | 'FOREIGN_CURRENCY'
  | 'PERIOD_NOT_UNDERSTOOD';

export type ExpenseRefused = {
  __typename?: 'ExpenseRefused';
  length?: Maybe<Scalars['Int']['output']>;
  message: Scalars['String']['output'];
  reason: ExpenseRefusalReason;
};

export type ExpenseResult = Expense | ExpenseNotFound;

export type ExpenseSaved = {
  __typename?: 'ExpenseSaved';
  expense: Expense;
};

export type ExpenseSummary = {
  __typename?: 'ExpenseSummary';
  count: Scalars['Int']['output'];
  end?: Maybe<Scalars['Date']['output']>;
  grandTotalPaise: Scalars['Paise']['output'];
  label: Scalars['String']['output'];
  phrase: Scalars['String']['output'];
  start?: Maybe<Scalars['Date']['output']>;
  totals: Array<ExpenseCategoryTotal>;
};

export type ExpensesFilterInput = {
  category?: InputMaybe<ExpenseCategory>;
  end?: InputMaybe<Scalars['Date']['input']>;
  start?: InputMaybe<Scalars['Date']['input']>;
};

export type ForgetMemoryResult = MemoriesForgotten | MemoryNotFound;

export type InvalidCredentials = {
  __typename?: 'InvalidCredentials';
  message: Scalars['String']['output'];
};

export type InvalidMemory = {
  __typename?: 'InvalidMemory';
  message: Scalars['String']['output'];
};

export type InvalidReminder = {
  __typename?: 'InvalidReminder';
  field: Scalars['String']['output'];
  message: Scalars['String']['output'];
};

export type InvalidReminderSettings = {
  __typename?: 'InvalidReminderSettings';
  field: Scalars['String']['output'];
  message: Scalars['String']['output'];
};

export type InvalidTimezone = {
  __typename?: 'InvalidTimezone';
  message: Scalars['String']['output'];
};

export type MalformedResult = {
  __typename?: 'MalformedResult';
  message: Scalars['String']['output'];
  reason: Scalars['String']['output'];
};

export type MarkAllNotificationsReadSucceeded = {
  __typename?: 'MarkAllNotificationsReadSucceeded';
  markedCount: Scalars['Int']['output'];
};

export type MarkNotificationReadResult = Notification | NotificationNotFound;

export type Me = {
  __typename?: 'Me';
  avatarUrl?: Maybe<Scalars['String']['output']>;
  email: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  username?: Maybe<Scalars['String']['output']>;
};

export type MemoriesFilterInput = {
  category?: InputMaybe<MemoryCategory>;
  uncategorised?: Scalars['Boolean']['input'];
};

export type MemoriesForgotten = {
  __typename?: 'MemoriesForgotten';
  count: Scalars['Int']['output'];
};

export type MemoriesListed = {
  __typename?: 'MemoriesListed';
  memories: Array<Memory>;
  searchText?: Maybe<Scalars['String']['output']>;
};

export type Memory = {
  __typename?: 'Memory';
  category?: Maybe<MemoryCategory>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  origin: Scalars['String']['output'];
  originalInput?: Maybe<Scalars['String']['output']>;
  text: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type MemoryCategory =
  | 'LIFE'
  | 'PEOPLE'
  | 'PERSONAL'
  | 'PROFESSIONAL';

export type MemoryConflictAsked = {
  __typename?: 'MemoryConflictAsked';
  category?: Maybe<MemoryCategory>;
  conflicting: Array<Memory>;
  newText: Scalars['String']['output'];
  pendingCaptureId: Scalars['ID']['output'];
  question: Scalars['String']['output'];
};

export type MemoryDiscarded = {
  __typename?: 'MemoryDiscarded';
  message: Scalars['String']['output'];
};

export type MemoryNotFound = {
  __typename?: 'MemoryNotFound';
  message: Scalars['String']['output'];
};

export type MemoryResult = Memory | MemoryNotFound;

export type MemorySaved = {
  __typename?: 'MemorySaved';
  memory: Memory;
  secretCaution?: Maybe<SecretKind>;
};

export type MemoryTooLong = {
  __typename?: 'MemoryTooLong';
  length: Scalars['Int']['output'];
  limit: Scalars['Int']['output'];
  message: Scalars['String']['output'];
};

export type Mutation = {
  __typename?: 'Mutation';
  answerPendingCapture: CaptureResult;
  completeTask: UpdateTaskResult;
  deleteEvent: DeleteEventResult;
  deleteExpense: DeleteExpenseResult;
  deleteReminder: DeleteReminderResult;
  deleteTask: Scalars['Int']['output'];
  discardPendingCapture: Scalars['Boolean']['output'];
  forgetMemory: ForgetMemoryResult;
  markAllNotificationsRead: MarkAllNotificationsReadSucceeded;
  markNotificationRead: MarkNotificationReadResult;
  markReminderDone: ReminderActionResult;
  recordSearchEvent: Scalars['Boolean']['output'];
  recordsViewOpened: Scalars['Boolean']['output'];
  resolveMemoryConflict: ResolveMemoryConflictResult;
  signIn: SignInResult;
  snoozeReminder: ReminderActionResult;
  submitCapture: CaptureResult;
  updateEvent: UpdateEventResult;
  updateExpense: UpdateExpenseResult;
  updateMemory: UpdateMemoryResult;
  updateReminder: UpdateReminderResult;
  updateReminderSettings: UpdateReminderSettingsResult;
  updateTask: UpdateTaskResult;
  updateTimezone: UpdateTimezoneResult;
};


export type MutationAnswerPendingCaptureArgs = {
  answer: Scalars['String']['input'];
  pendingCaptureId: Scalars['ID']['input'];
};


export type MutationCompleteTaskArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteEventArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteExpenseArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteReminderArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteTaskArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationDiscardPendingCaptureArgs = {
  pendingCaptureId: Scalars['ID']['input'];
};


export type MutationForgetMemoryArgs = {
  id: Scalars['ID']['input'];
};


export type MutationMarkNotificationReadArgs = {
  id: Scalars['ID']['input'];
};


export type MutationMarkReminderDoneArgs = {
  id: Scalars['ID']['input'];
};


export type MutationRecordSearchEventArgs = {
  input: RecordSearchEventInput;
};


export type MutationResolveMemoryConflictArgs = {
  answer: ConflictAnswer;
  pendingCaptureId: Scalars['ID']['input'];
};


export type MutationSignInArgs = {
  input: SignInInput;
};


export type MutationSnoozeReminderArgs = {
  id: Scalars['ID']['input'];
  option: SnoozeChoice;
};


export type MutationSubmitCaptureArgs = {
  rawInput: Scalars['String']['input'];
};


export type MutationUpdateEventArgs = {
  id: Scalars['ID']['input'];
  input: EventInput;
};


export type MutationUpdateExpenseArgs = {
  id: Scalars['ID']['input'];
  input: UpdateExpenseInput;
};


export type MutationUpdateMemoryArgs = {
  id: Scalars['ID']['input'];
  input: UpdateMemoryInput;
};


export type MutationUpdateReminderArgs = {
  id: Scalars['ID']['input'];
  input: UpdateReminderInput;
};


export type MutationUpdateReminderSettingsArgs = {
  input: UpdateReminderSettingsInput;
};


export type MutationUpdateTaskArgs = {
  id: Scalars['ID']['input'];
  input: UpdateTaskInput;
};


export type MutationUpdateTimezoneArgs = {
  input: UpdateTimezoneInput;
};

export type NoFieldsToUpdate = {
  __typename?: 'NoFieldsToUpdate';
  message: Scalars['String']['output'];
};

export type NonCommandGuidance = {
  __typename?: 'NonCommandGuidance';
  originalInput: Scalars['String']['output'];
};

export type Notification = {
  __typename?: 'Notification';
  actedAt?: Maybe<Scalars['DateTime']['output']>;
  action?: Maybe<NotificationAction>;
  /** Event alerts only: the alert Done and Snooze act on. */
  actionTargetId?: Maybe<Scalars['ID']['output']>;
  createdAt: Scalars['DateTime']['output'];
  detail: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  kind: NotificationKind;
  marker: NotificationMarker;
  occurredAt: Scalars['DateTime']['output'];
  read: Scalars['Boolean']['output'];
  showPopup: Scalars['Boolean']['output'];
  targetId?: Maybe<Scalars['ID']['output']>;
  title: Scalars['String']['output'];
};

export type NotificationAction =
  | 'DONE'
  | 'SNOOZED';

export type NotificationKind =
  | 'EMAIL_PAUSED'
  | 'EVENT_ALERT'
  | 'REMINDER';

export type NotificationMarker =
  | 'LATE'
  | 'MISSED'
  | 'NONE';

export type NotificationNotFound = {
  __typename?: 'NotificationNotFound';
  message: Scalars['String']['output'];
};

export type NotificationPage = {
  __typename?: 'NotificationPage';
  items: Array<Notification>;
  nextCursor?: Maybe<Scalars['String']['output']>;
};

export type PendingCaptureNotFound = {
  __typename?: 'PendingCaptureNotFound';
  message: Scalars['String']['output'];
};

export type PendingQuestionCreated = {
  __typename?: 'PendingQuestionCreated';
  pendingCaptureId: Scalars['ID']['output'];
  question: Scalars['String']['output'];
};

export type ProviderTimeout = {
  __typename?: 'ProviderTimeout';
  budgetSeconds: Scalars['Float']['output'];
  message: Scalars['String']['output'];
};

export type ProviderUnavailable = {
  __typename?: 'ProviderUnavailable';
  message: Scalars['String']['output'];
};

export type Query = {
  __typename?: 'Query';
  apiVersion: Scalars['String']['output'];
  captureHistory: CaptureHistoryPage;
  event: EventResult;
  events: Array<Event>;
  expense: ExpenseResult;
  expensePeriods: Array<ExpensePeriod>;
  expenseSummary: ExpenseSummary;
  expenses: Array<Expense>;
  me: Me;
  memories: Array<Memory>;
  memory: MemoryResult;
  notifications: NotificationPage;
  record: RecordResult;
  records: Array<RecordItem>;
  relatedRecords: Array<SearchRecord>;
  reminder: ReminderResult;
  reminders: ReminderGroups;
  search: SearchPageResult;
  settings: Settings;
  tasks: Array<Task>;
  unreadNotificationCount: Scalars['Int']['output'];
};


export type QueryCaptureHistoryArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryEventArgs = {
  id: Scalars['ID']['input'];
};


export type QueryEventsArgs = {
  scope?: EventScope;
};


export type QueryExpenseArgs = {
  id: Scalars['ID']['input'];
};


export type QueryExpenseSummaryArgs = {
  filter?: InputMaybe<ExpensesFilterInput>;
};


export type QueryExpensesArgs = {
  filter?: InputMaybe<ExpensesFilterInput>;
};


export type QueryMemoriesArgs = {
  filter?: InputMaybe<MemoriesFilterInput>;
};


export type QueryMemoryArgs = {
  id: Scalars['ID']['input'];
};


export type QueryNotificationsArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
};


export type QueryRecordArgs = {
  id: Scalars['ID']['input'];
};


export type QueryRecordsArgs = {
  filter?: InputMaybe<RecordsFilterInput>;
};


export type QueryRelatedRecordsArgs = {
  id: Scalars['ID']['input'];
  recordType: RecordType;
};


export type QueryReminderArgs = {
  id: Scalars['ID']['input'];
};


export type QuerySearchArgs = {
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
  recordType?: InputMaybe<RecordType>;
  text: Scalars['String']['input'];
};


export type QuerySettingsArgs = {
  detectedTimezone?: InputMaybe<Scalars['String']['input']>;
};

export type RecordItem = Event | Expense | Memory | Reminder | Task;

export type RecordNotFound = {
  __typename?: 'RecordNotFound';
  message: Scalars['String']['output'];
};

export type RecordResult = RecordNotFound | Task;

export type RecordSearchEventInput = {
  kind: SearchEventKind;
  position: Scalars['Int']['input'];
};

export type RecordType =
  | 'EVENT'
  | 'EXPENSE'
  | 'MEMORY'
  | 'REMINDER'
  | 'TASK';

export type RecordsFilterInput = {
  kind?: InputMaybe<Scalars['String']['input']>;
  sortBy?: SortField;
  sortDesc?: Scalars['Boolean']['input'];
};

export type Reminder = {
  __typename?: 'Reminder';
  anchorLocalDate: Scalars['Date']['output'];
  createdAt: Scalars['DateTime']['output'];
  description: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  lastAction?: Maybe<ReminderAction>;
  lastFiredAt?: Maybe<Scalars['DateTime']['output']>;
  localTime: Scalars['String']['output'];
  nextFireAt?: Maybe<Scalars['DateTime']['output']>;
  origin: Scalars['String']['output'];
  originalInput?: Maybe<Scalars['String']['output']>;
  repeatInterval: Scalars['Int']['output'];
  repeatKind: ReminderRepeatKind;
  repeatMonthDay?: Maybe<Scalars['Int']['output']>;
  repeatText: Scalars['String']['output'];
  repeatWeekdays: Array<Scalars['Int']['output']>;
  scheduleTimezone: Scalars['String']['output'];
  snoozedUntil?: Maybe<Scalars['DateTime']['output']>;
  state: ReminderState;
  updatedAt: Scalars['DateTime']['output'];
  /** Why the time differs from what was typed. Only on create. */
  whenNote?: Maybe<Scalars['String']['output']>;
  whenText: Scalars['String']['output'];
};

export type ReminderAction =
  | 'DONE'
  | 'MISSED'
  | 'SNOOZED';

export type ReminderActionResult = Reminder | ReminderNotFound;

export type ReminderCreated = {
  __typename?: 'ReminderCreated';
  reminder: Reminder;
};

export type ReminderDeleteSucceeded = {
  __typename?: 'ReminderDeleteSucceeded';
  id: Scalars['ID']['output'];
};

export type ReminderDeleted = {
  __typename?: 'ReminderDeleted';
  message: Scalars['String']['output'];
};

export type ReminderGroups = {
  __typename?: 'ReminderGroups';
  done: Array<Reminder>;
  needsAttention: Array<Reminder>;
  upcoming: Array<Reminder>;
};

export type ReminderLimitReached = {
  __typename?: 'ReminderLimitReached';
  limit: Scalars['Int']['output'];
  message: Scalars['String']['output'];
};

export type ReminderNotFound = {
  __typename?: 'ReminderNotFound';
  message: Scalars['String']['output'];
};

export type ReminderRepeatKind =
  | 'DAILY'
  | 'MONTHLY'
  | 'NONE'
  | 'WEEKLY'
  | 'YEARLY';

export type ReminderResult = Reminder | ReminderNotFound;

export type ReminderSettingsSaved = {
  __typename?: 'ReminderSettingsSaved';
  settings: Settings;
  showBothOffWarning: Scalars['Boolean']['output'];
};

export type ReminderState =
  | 'DONE'
  | 'FIRED'
  | 'UPCOMING';

export type ReminderTimePassed = {
  __typename?: 'ReminderTimePassed';
  message: Scalars['String']['output'];
};

export type RemindersListed = {
  __typename?: 'RemindersListed';
  reminders: Array<Reminder>;
};

export type ResolveMemoryConflictResult = MemoryDiscarded | MemorySaved | PendingCaptureNotFound;

export type SearchAnswer = {
  __typename?: 'SearchAnswer';
  sentences: Array<AnswerSentence>;
};

export type SearchEventKind =
  | 'ANSWER_CITATION_OPENED'
  | 'RELATED_OPENED'
  | 'SEARCH_RESULT_OPENED';

export type SearchGroup = {
  __typename?: 'SearchGroup';
  hits: Array<SearchHit>;
  recordType: RecordType;
  total: Scalars['Int']['output'];
};

export type SearchHit = {
  __typename?: 'SearchHit';
  citation?: Maybe<Scalars['Int']['output']>;
  record: SearchRecord;
};

export type SearchPage = {
  __typename?: 'SearchPage';
  hits: Array<SearchRecord>;
  meaningUnavailable: Scalars['Boolean']['output'];
  otherTypesTotal: Scalars['Int']['output'];
  query: Scalars['String']['output'];
  total: Scalars['Int']['output'];
};

export type SearchPageResult = SearchPage | SearchTooLong;

export type SearchRecord = Event | Expense | Memory | Reminder | Task;

export type SearchResults = {
  __typename?: 'SearchResults';
  answer?: Maybe<SearchAnswer>;
  answerLimitReached: Scalars['Boolean']['output'];
  answerUnavailable: Scalars['Boolean']['output'];
  groups: Array<SearchGroup>;
  meaningUnavailable: Scalars['Boolean']['output'];
  noSupport: Scalars['Boolean']['output'];
  query: Scalars['String']['output'];
};

export type SearchTooLong = {
  __typename?: 'SearchTooLong';
  length: Scalars['Int']['output'];
  limit: Scalars['Int']['output'];
};

export type SecretKind =
  | 'CARD'
  | 'CREDENTIAL'
  | 'ID_NUMBER'
  | 'TAX_ID';

export type Settings = {
  __typename?: 'Settings';
  defaultReminderTime: Scalars['String']['output'];
  emailEnabled: Scalars['Boolean']['output'];
  popupsEnabled: Scalars['Boolean']['output'];
  timezone: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type SharedQuotaExhausted = {
  __typename?: 'SharedQuotaExhausted';
  message: Scalars['String']['output'];
};

export type SignInInput = {
  email: Scalars['String']['input'];
  password: Scalars['String']['input'];
};

export type SignInResult = AccountLocked | AccountNotVerified | AuthProviderUnavailable | InvalidCredentials | SignedIn;

export type SignedIn = {
  __typename?: 'SignedIn';
  accessToken: Scalars['String']['output'];
  expiresIn: Scalars['Int']['output'];
  refreshToken: Scalars['String']['output'];
};

export type SnoozeChoice =
  | 'ONE_HOUR'
  | 'TEN_MINUTES'
  | 'TOMORROW';

export type SortField =
  | 'CREATED_AT'
  | 'DUE_AT';

export type Subscription = {
  __typename?: 'Subscription';
  notificationReceived: Notification;
};

export type Task = {
  __typename?: 'Task';
  createdAt: Scalars['DateTime']['output'];
  dueAt?: Maybe<Scalars['DateTime']['output']>;
  id: Scalars['ID']['output'];
  isOverdue: Scalars['Boolean']['output'];
  origin: Scalars['String']['output'];
  originalInput?: Maybe<Scalars['String']['output']>;
  status: Scalars['String']['output'];
  title: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type TaskCreated = {
  __typename?: 'TaskCreated';
  task: Task;
};

export type TaskStatus =
  | 'DONE'
  | 'PENDING';

export type TasksListed = {
  __typename?: 'TasksListed';
  tasks: Array<Task>;
};

export type UnrecognisedCommand = {
  __typename?: 'UnrecognisedCommand';
  attemptedName: Scalars['String']['output'];
  closestMatches: Array<Scalars['String']['output']>;
};

export type UpdateEventResult = EventInvalid | EventNotFound | EventUpdated;

export type UpdateExpenseInput = {
  amountPaise?: InputMaybe<Scalars['Paise']['input']>;
  category?: InputMaybe<ExpenseCategory>;
  description?: InputMaybe<Scalars['String']['input']>;
  spentOn?: InputMaybe<Scalars['Date']['input']>;
};

export type UpdateExpenseResult = Expense | ExpenseInvalid | ExpenseNotFound;

export type UpdateMemoryInput = {
  category?: InputMaybe<MemoryCategory>;
  text: Scalars['String']['input'];
};

export type UpdateMemoryResult = InvalidMemory | Memory | MemoryNotFound | MemoryTooLong;

export type UpdateReminderInput = {
  description: Scalars['String']['input'];
  localTime: Scalars['String']['input'];
  repeatInterval?: Scalars['Int']['input'];
  repeatKind: ReminderRepeatKind;
  repeatWeekdays?: Array<Scalars['Int']['input']>;
  startDate: Scalars['Date']['input'];
};

export type UpdateReminderResult = InvalidReminder | Reminder | ReminderDeleted | ReminderNotFound | ReminderTimePassed;

export type UpdateReminderSettingsInput = {
  defaultReminderTime?: InputMaybe<Scalars['String']['input']>;
  emailEnabled?: InputMaybe<Scalars['Boolean']['input']>;
  popupsEnabled?: InputMaybe<Scalars['Boolean']['input']>;
};

export type UpdateReminderSettingsResult = InvalidReminderSettings | ReminderSettingsSaved;

export type UpdateTaskInput = {
  dueAt?: InputMaybe<Scalars['DateTime']['input']>;
  status?: InputMaybe<TaskStatus>;
  title?: InputMaybe<Scalars['String']['input']>;
};

export type UpdateTaskResult = NoFieldsToUpdate | RecordNotFound | Task;

export type UpdateTimezoneInput = {
  timezone: Scalars['String']['input'];
};

export type UpdateTimezoneResult = InvalidTimezone | Settings;

export type UserLimitReached = {
  __typename?: 'UserLimitReached';
  limit: Scalars['Int']['output'];
  message: Scalars['String']['output'];
  resetsAt: Scalars['DateTime']['output'];
};
