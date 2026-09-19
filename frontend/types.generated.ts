export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** Date with time (isoformat) */
  DateTime: { input: string; output: string; }
};

export type CaptureHistoryPage = {
  __typename?: 'CaptureHistoryPage';
  items: Array<CaptureTurn>;
  nextCursor?: Maybe<Scalars['String']['output']>;
};

export type CaptureResult = MalformedResult | NonCommandGuidance | PendingQuestionCreated | ProviderTimeout | ProviderUnavailable | SharedQuotaExhausted | TaskCreated | TasksListed | UnrecognisedCommand | UserLimitReached;

export type CaptureTurn = {
  __typename?: 'CaptureTurn';
  answerText?: Maybe<Scalars['String']['output']>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  inputText: Scalars['String']['output'];
  outcome: CaptureTurnOutcome;
  questionText?: Maybe<Scalars['String']['output']>;
  resultingPendingCaptureId?: Maybe<Scalars['ID']['output']>;
  resultingTaskId?: Maybe<Scalars['ID']['output']>;
};

export type CaptureTurnOutcome =
  | 'DISCARDED'
  | 'QUESTION_ASKED'
  | 'REFUSED'
  | 'TASK_CREATED';

export type InvalidTimezone = {
  __typename?: 'InvalidTimezone';
  message: Scalars['String']['output'];
};

export type MalformedResult = {
  __typename?: 'MalformedResult';
  message: Scalars['String']['output'];
  reason: Scalars['String']['output'];
};

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
  deleteTask: Scalars['Int']['output'];
  discardPendingCapture: Scalars['Boolean']['output'];
  recordsViewOpened: Scalars['Boolean']['output'];
  submitCapture: CaptureResult;
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


export type MutationDeleteTaskArgs = {
  ids: Array<Scalars['ID']['input']>;
};


export type MutationDiscardPendingCaptureArgs = {
  pendingCaptureId: Scalars['ID']['input'];
};


export type MutationSubmitCaptureArgs = {
  rawInput: Scalars['String']['input'];
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
  record: RecordResult;
  records: Array<Task>;
  settings: Settings;
  tasks: Array<Task>;
};


export type QueryCaptureHistoryArgs = {
  cursor?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
};


export type QueryRecordArgs = {
  id: Scalars['ID']['input'];
};


export type QueryRecordsArgs = {
  filter?: InputMaybe<RecordsFilterInput>;
};


export type QuerySettingsArgs = {
  detectedTimezone?: InputMaybe<Scalars['String']['input']>;
};

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

export type Settings = {
  __typename?: 'Settings';
  timezone: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export type SharedQuotaExhausted = {
  __typename?: 'SharedQuotaExhausted';
  message: Scalars['String']['output'];
};

export type SortField =
  | 'CREATED_AT'
  | 'DUE_AT';

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
