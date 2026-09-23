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

export type AuthProviderUnavailable = {
  __typename?: 'AuthProviderUnavailable';
  message: Scalars['String']['output'];
};

export type CaptureHistoryPage = {
  __typename?: 'CaptureHistoryPage';
  items: Array<CaptureTurn>;
  nextCursor?: Maybe<Scalars['String']['output']>;
};

export type CaptureResult = MalformedResult | NonCommandGuidance | PendingQuestionCreated | ProviderTimeout | ProviderUnavailable | ReminderCreated | ReminderLimitReached | RemindersListed | SharedQuotaExhausted | TaskCreated | TasksListed | UnrecognisedCommand | UserLimitReached;

export type CaptureTurn = {
  __typename?: 'CaptureTurn';
  answerText?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  inputText: Scalars['String']['output'];
  outcome: CaptureTurnOutcome;
  questionText?: Maybe<Scalars['String']['output']>;
  resultingPendingCaptureId?: Maybe<Scalars['ID']['output']>;
  resultingReminderId?: Maybe<Scalars['ID']['output']>;
  resultingTaskId?: Maybe<Scalars['ID']['output']>;
};

export type CaptureTurnOutcome =
  | 'DISCARDED'
  | 'QUESTION_ASKED'
  | 'REFUSED'
  | 'REMINDER_CREATED'
  | 'TASK_CREATED';

export type DeleteReminderResult = ReminderDeleteSucceeded | ReminderNotFound;

export type InvalidCredentials = {
  __typename?: 'InvalidCredentials';
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

export type Mutation = {
  __typename?: 'Mutation';
  answerPendingCapture: CaptureResult;
  completeTask: UpdateTaskResult;
  deleteReminder: DeleteReminderResult;
  deleteTask: Scalars['Int']['output'];
  discardPendingCapture: Scalars['Boolean']['output'];
  markAllNotificationsRead: MarkAllNotificationsReadSucceeded;
  markNotificationRead: MarkNotificationReadResult;
  markReminderDone: ReminderActionResult;
  recordsViewOpened: Scalars['Boolean']['output'];
  signIn: SignInResult;
  snoozeReminder: ReminderActionResult;
  submitCapture: CaptureResult;
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


export type MutationDeleteReminderArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteTaskArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationDiscardPendingCaptureArgs = {
  pendingCaptureId: Scalars['ID']['input'];
};


export type MutationMarkNotificationReadArgs = {
  id: Scalars['ID']['input'];
};


export type MutationMarkReminderDoneArgs = {
  id: Scalars['ID']['input'];
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
  me: Me;
  notifications: NotificationPage;
  record: RecordResult;
  records: Array<RecordItem>;
  reminder: ReminderResult;
  reminders: ReminderGroups;
  settings: Settings;
  tasks: Array<Task>;
  unreadNotificationCount: Scalars['Int']['output'];
};


export type QueryCaptureHistoryArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
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


export type QueryReminderArgs = {
  id: Scalars['ID']['input'];
};


export type QueryRemindersArgs = {
  search?: InputMaybe<Scalars['String']['input']>;
};


export type QuerySettingsArgs = {
  detectedTimezone?: InputMaybe<Scalars['String']['input']>;
};

export type RecordItem = Reminder | Task;

export type RecordNotFound = {
  __typename?: 'RecordNotFound';
  message: Scalars['String']['output'];
};

export type RecordResult = RecordNotFound | Task;

export type RecordsFilterInput = {
  kind?: InputMaybe<Scalars['String']['input']>;
  search?: InputMaybe<Scalars['String']['input']>;
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
