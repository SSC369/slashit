import { AlertCircle, AlertTriangle, ArrowRight, Check, Clock, Search, Sparkles } from "lucide-react";
import { Fragment, type KeyboardEvent, type ReactElement } from "react";

import CategoryTag from "../../../components/CategoryTag";
import ExpenseMarker from "../../../components/ExpenseMarker";
import ReminderStatusPill from "../../../components/ReminderStatusPill";
import Button from "../../../design-system/components/Button";
import type { SearchResultsFieldsFragment } from "../../../fragments/SearchResultsFields.generated";
import type { RecordType, SearchEventKind } from "../../../../types.generated";
import { cn } from "../../../utils/cn";
import { formatShortDate } from "../../../utils/formatDate";
import { formatDayShort } from "../../../utils/localDate";
import { formatRupees, parseRupees, spokenRupees } from "../../../utils/money";
import * as Styles from "./styles";

type SearchGroupFragment = SearchResultsFieldsFragment["groups"][number];
export type SearchRecordFragment = SearchGroupFragment["hits"][number]["record"];
type SearchAnswerFragment = NonNullable<SearchResultsFieldsFragment["answer"]>;

/** What an open is recorded as (PRD §8): a row's place down the card, or the citation followed. */
export interface SearchOpenEvent {
  kind: SearchEventKind;
  position: number;
}

type OpenSearchRecord = (record: SearchRecordFragment, opened: SearchOpenEvent) => void;

const GROUP_LABEL: Record<RecordType, string> = {
  TASK: "Tasks",
  REMINDER: "Reminders",
  MEMORY: "Memories",
  EXPENSE: "Expenses",
};

const GROUP_MARKER: Record<RecordType, ReactElement> = {
  TASK: <span className={Styles.typeDotTaskStyles} />,
  REMINDER: <span className={Styles.typeDotReminderStyles} />,
  MEMORY: <span className={Styles.typeDotMemoryStyles} />,
  // 006 design change 2026-10-03: the ₹ marker, as in Records.
  EXPENSE: <ExpenseMarker />,
};

interface SearchResultsCardProps {
  results: SearchResultsFieldsFragment;
  onOpenRecord: OpenSearchRecord;
  onSeeAll: (recordType: RecordType | null, query: string) => void;
}

/**
 * `Main`, `SearchPassport`, `SearchResults`, `SearchNoSupport`, `SearchDegraded`
 * (FR-7 to FR-10, FR-15 to FR-20).
 */
export const SearchResultsCard = (props: SearchResultsCardProps): ReactElement => {
  const { results, onOpenRecord, onSeeAll } = props;
  const matchCount = results.groups.reduce((sum, group) => sum + group.total, 0);
  const hasMatches = results.groups.length > 0;
  const hits = results.groups.flatMap((group) => group.hits);
  const positions = new Map(hits.map((hit, index) => [hit.record.id, index + 1]));
  const citedRecords = new Map(
    hits.flatMap((hit) => (hit.citation === null ? [] : [[hit.citation, hit.record] as const])),
  );
  const openRow = (record: SearchRecordFragment): void =>
    onOpenRecord(record, { kind: "SEARCH_RESULT_OPENED", position: positions.get(record.id) ?? 1 });
  const strips = (
    <>
      {results.answerUnavailable &&
        (results.answerLimitReached ? <AnswerLimitStrip /> : <AnswerUnavailableStrip />)}
      {results.meaningUnavailable && <MeaningUnavailableStrip />}
    </>
  );

  if (!hasMatches) {
    return (
      <div className={Styles.cardStyles}>
        <div className={Styles.cardHeadStyles}>
          {results.noSupport ? (
            <NoAnswerPill />
          ) : (
            <span className={cn(Styles.pillBaseStyles, Styles.pillMutedStyles)}>
              <Search size={12} className="shrink-0" />
              <span className="truncate">No records match “{results.query}”</span>
            </span>
          )}
        </div>
        {strips}
        {results.noSupport ? (
          <NoSupportBlock query={results.query} />
        ) : (
          <div className={Styles.searchNoMatchBodyStyles}>
            {results.meaningUnavailable
              ? "Nothing you have recorded matches by word."
              : "Nothing you have recorded matches by word or by meaning."}
          </div>
        )}
        <div className={Styles.cardFootStyles}>
          <span>Searched tasks, reminders and memories</span>
          <Button size="sm" onClick={() => onSeeAll(null, "")}>
            Browse Records <ArrowRight size={14} />
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <SearchCountPill results={results} matchCount={matchCount} />
      </div>
      {strips}
      {results.answer !== null && (
        <AnswerBlock
          answer={results.answer}
          citedRecords={citedRecords}
          onOpenCitation={(record, citation) =>
            onOpenRecord(record, { kind: "ANSWER_CITATION_OPENED", position: citation })
          }
        />
      )}
      {results.noSupport && <NoSupportBlock query={results.query} />}
      {results.groups.map((group, index) => (
        <SearchGroup
          key={group.recordType}
          group={group}
          isFirst={index === 0}
          query={results.query}
          onOpenRow={openRow}
          onSeeAll={onSeeAll}
        />
      ))}
      <div className={Styles.cardFootStyles}>
        <span>
          {/* 006 design §8 (`SearchExpense`, FR-30): said only when the search is a number. */}
          {parseRupees(results.query) === null
            ? "Best match first · only your records are searched"
            : "A number also matches expenses of exactly that amount"}
        </span>
        <Button size="sm" onClick={() => onSeeAll(null, results.query)}>
          Open in Records <ArrowRight size={14} />
        </Button>
      </div>
    </div>
  );
};

interface SearchCountPillProps {
  results: SearchResultsFieldsFragment;
  matchCount: number;
}

/** A question's card counts records found; a word search's names what matched. */
const SearchCountPill = (props: SearchCountPillProps): ReactElement => {
  const { results, matchCount } = props;
  if (results.noSupport) return <NoAnswerPill />;

  const isQuestion = results.answer !== null || results.answerUnavailable;
  const label = isQuestion
    ? `${matchCount} ${matchCount === 1 ? "record" : "records"} found${results.answer !== null ? " · 1 answer" : ""}`
    : `${matchCount} ${matchCount === 1 ? "record matches" : "records match"} “${results.query}”`;

  return (
    <span className={cn(Styles.pillBaseStyles, Styles.pillDoneStyles)}>
      <Check size={13} /> {label}
    </span>
  );
};

const NoAnswerPill = (): ReactElement => (
  <span className={cn(Styles.pillBaseStyles, Styles.pillMutedStyles)}>No answer in your records</span>
);

interface AnswerBlockProps {
  answer: SearchAnswerFragment;
  citedRecords: Map<number, SearchRecordFragment>;
  onOpenCitation: (record: SearchRecordFragment, citation: number) => void;
}

/** `Main`, FR-16 and FR-17: every sentence ends in the markers of what it cites. */
const AnswerBlock = (props: AnswerBlockProps): ReactElement => {
  const { answer, citedRecords, onOpenCitation } = props;

  return (
    <section aria-label="Answer from your records" className={Styles.answerBlockStyles}>
      <AnswerLabel />
      {answer.sentences.map((sentence, index) => (
        <Fragment key={index}>
          {index > 0 && " "}
          {sentence.text}
          {sentence.citations.map((citation) => {
            const record = citedRecords.get(citation);
            return record === undefined ? null : (
              <button
                key={citation}
                type="button"
                className={Styles.citeMarkerStyles}
                aria-label={`source ${citation}: ${recordTitle(record)}`}
                onClick={() => onOpenCitation(record, citation)}
              >
                {citation}
              </button>
            );
          })}
        </Fragment>
      ))}
    </section>
  );
};

/**
 * `SearchNoSupport`, FR-18: states that nothing answers, and nothing else.
 * Quotes the question as typed: the server returns no rephrasing of it.
 */
const NoSupportBlock = (props: { query: string }): ReactElement => (
  <section aria-label="Answer from your records" className={Styles.answerBlockStyles}>
    <AnswerLabel />
    <span className={Styles.answerNoSupportStyles}>
      Nothing you have saved answers “{props.query}”. Save it with{" "}
      <span className={Styles.answerCommandStyles}>/remember</span> and Slashit can answer next time.
    </span>
  </section>
);

const AnswerLabel = (): ReactElement => (
  <div className={Styles.answerLabelStyles}>
    <Sparkles size={14} /> Answer from your records
  </div>
);

interface SearchGroupProps {
  group: SearchGroupFragment;
  isFirst: boolean;
  query: string;
  onOpenRow: (record: SearchRecordFragment) => void;
  onSeeAll: (recordType: RecordType | null, query: string) => void;
}

/** Design delta `.ghead` and `.hit`: one type, at most five, best first. */
const SearchGroup = (props: SearchGroupProps): ReactElement => {
  const { group, isFirst, query, onOpenRow, onSeeAll } = props;
  const hasMore = group.total > group.hits.length;

  return (
    <div className={cn(Styles.searchGroupStyles, !isFirst && Styles.searchGroupSeparatorStyles)}>
      <div className={Styles.searchGroupHeadStyles}>
        <span className={Styles.searchGroupLabelStyles}>
          {GROUP_MARKER[group.recordType]}
          {GROUP_LABEL[group.recordType]}
        </span>
        {hasMore ? (
          <Button size="sm" onClick={() => onSeeAll(group.recordType, query)}>
            See all {group.total} in Records <ArrowRight size={14} />
          </Button>
        ) : (
          <span className={Styles.searchGroupCountStyles}>
            {group.total} {group.total === 1 ? "match" : "matches"}
          </span>
        )}
      </div>
      {group.hits.map((hit) => (
        <SearchHitRow
          key={hit.record.id}
          record={hit.record}
          citation={hit.citation}
          onOpenRow={onOpenRow}
        />
      ))}
    </div>
  );
};

interface SearchHitRowProps {
  record: SearchRecordFragment;
  citation: number | null;
  onOpenRow: (record: SearchRecordFragment) => void;
}

/** FR-9: type, title, date and status, as the records table shows them. FR-17: its marker. */
const SearchHitRow = (props: SearchHitRowProps): ReactElement => {
  const { record, citation, onOpenRow } = props;
  const openOnEnter = (event: KeyboardEvent<HTMLDivElement>): void => {
    if (event.key === "Enter") onOpenRow(record);
  };

  return (
    <div
      role="button"
      tabIndex={0}
      className={Styles.searchHitRowStyles}
      onClick={() => onOpenRow(record)}
      onKeyDown={openOnEnter}
    >
      <SearchHitCells record={record} citation={citation} />
    </div>
  );
};

const RowCitation = (props: { citation: number | null }): ReactElement | null =>
  props.citation === null ? null : (
    <span
      aria-label={`cited as ${props.citation}`}
      className={cn(Styles.citeMarkerStyles, Styles.citeMarkerRowStyles)}
    >
      {props.citation}
    </span>
  );

const recordTitle = (record: SearchRecordFragment): string => {
  switch (record.__typename) {
    case "Task":
      return record.title;
    case "Reminder":
      return record.description;
    case "Memory":
      return record.text;
    case "Expense":
      return record.description;
    default:
      return assertNever(record);
  }
};

const SearchHitCells = (props: {
  record: SearchRecordFragment;
  citation: number | null;
}): ReactElement => {
  const { record, citation } = props;

  switch (record.__typename) {
    case "Task": {
      const isDone = record.status === "DONE";
      return (
        <>
          <span className={Styles.searchHitTitleStyles}>{record.title}</span>
          <RowCitation citation={citation} />
          <span className={Styles.searchHitDateStyles}>{formatShortDate(record.dueAt)}</span>
          <span className={Styles.searchHitStatusStyles}>
            <span
              className={cn(
                Styles.pillBaseStyles,
                isDone ? Styles.pillDoneStyles : Styles.pillPendingStyles,
              )}
            >
              {isDone ? "Done" : "Pending"}
            </span>
          </span>
        </>
      );
    }
    case "Reminder":
      return (
        <>
          <span className={Styles.searchHitTitleStyles}>{record.description}</span>
          <RowCitation citation={citation} />
          <span className={Styles.searchHitDateStyles}>{record.whenText}</span>
          <span className={Styles.searchHitStatusStyles}>
            <ReminderStatusPill reminder={record} />
          </span>
        </>
      );
    case "Memory":
      return (
        <>
          <span className={Styles.searchHitTitleStyles}>{record.text}</span>
          <RowCitation citation={citation} />
          <span className={Styles.searchHitDateStyles}>{formatShortDate(record.createdAt)}</span>
          <span className={Styles.searchHitStatusStyles}>
            <CategoryTag category={record.category} />
          </span>
        </>
      );
    // 006 `SearchExpense`: the day spent, and the amount where others show a status.
    case "Expense":
      return (
        <>
          <span className={Styles.searchHitTitleStyles}>{record.description}</span>
          <RowCitation citation={citation} />
          <span className={Styles.searchHitDateStyles}>{formatDayShort(record.spentOn)}</span>
          <span className={cn(Styles.searchHitStatusStyles, Styles.amountStyles)} aria-label={spokenRupees(record.amountPaise)}>
            {formatRupees(record.amountPaise)}
          </span>
        </>
      );
    default:
      return assertNever(record);
  }
};

const assertNever = (value: never): never => {
  throw new Error(`Unhandled search record type: ${JSON.stringify(value)}`);
};

/** `SearchDegraded`, FR-19: the model or the shared quota is out; the records stand. */
const AnswerUnavailableStrip = (): ReactElement => (
  <div className={Styles.searchStripStyles}>
    <AlertTriangle size={14} className="shrink-0" />
    <span>
      No answer this time: Slashit’s AI model is unavailable right now. Your matching records are
      below. This is temporary.
    </span>
  </div>
);

/** Dev log Q7: the answer was refused for the daily allowance, not an outage. */
const AnswerLimitStrip = (): ReactElement => (
  <div className={Styles.searchStripStyles}>
    <AlertTriangle size={14} className="shrink-0" />
    <span>You have used today’s AI answers. Your matching records are below.</span>
  </div>
);

/** `SearchDegraded`, FR-20. */
const MeaningUnavailableStrip = (): ReactElement => (
  <div className={Styles.searchStripStyles}>
    <AlertTriangle size={14} className="shrink-0" />
    <span>
      Showing word matches only. Matching by meaning is unavailable right now, so results may be
      incomplete.
    </span>
  </div>
);

interface SearchTooLongNoteProps {
  length: number;
  limit: number;
}

/** `SearchStates`, FR-3: the text is back in the box to shorten. */
export const SearchTooLongNote = (props: SearchTooLongNoteProps): ReactElement => {
  const { length, limit } = props;
  return (
    <div className={cn(Styles.noteBaseStyles, Styles.noteErrStyles)}>
      <AlertCircle size={18} className="shrink-0 text-destructive" />
      <div className="text-[13.5px] text-foreground">
        <b>That is {length} characters.</b> A search can be up to {limit}. What you typed is still
        in the box.
      </div>
    </div>
  );
};

/** `SearchStates`: a question's longer wait is explained (NFR-4). */
export const SearchLoadingCard = (props: { isQuestion: boolean }): ReactElement => (
  <div className={Styles.cardStyles}>
    <div className={Styles.cardHeadStyles}>
      <span className={cn(Styles.pillBaseStyles, Styles.pillWaitStyles)}>
        <Clock size={13} />{" "}
        {props.isQuestion ? "Reading your records to answer…" : "Searching your records…"}
      </span>
    </div>
    <div className="flex flex-col gap-3 px-4 py-3.5">
      <div className="h-[11px] w-[70%] animate-pulse rounded bg-border" />
      <div className="h-[11px] w-[52%] animate-pulse rounded bg-border" />
      <div className="h-[11px] w-[61%] animate-pulse rounded bg-border" />
    </div>
  </div>
);
