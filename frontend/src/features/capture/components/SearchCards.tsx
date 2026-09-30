import { AlertCircle, AlertTriangle, ArrowRight, Check, Clock, Search } from "lucide-react";
import type { ReactElement } from "react";

import CategoryTag from "../../../components/CategoryTag";
import ReminderStatusPill from "../../../components/ReminderStatusPill";
import Button from "../../../design-system/components/Button";
import type { SearchResultsFieldsFragment } from "../../../fragments/SearchResultsFields.generated";
import type { RecordType } from "../../../../types.generated";
import { cn } from "../../../utils/cn";
import { formatShortDate } from "../../../utils/formatDate";
import * as Styles from "./styles";

type SearchGroupFragment = SearchResultsFieldsFragment["groups"][number];
export type SearchRecordFragment = SearchGroupFragment["hits"][number]["record"];

const GROUP_LABEL: Record<RecordType, string> = {
  TASK: "Tasks",
  REMINDER: "Reminders",
  MEMORY: "Memories",
};

const GROUP_DOT: Record<RecordType, string> = {
  TASK: Styles.typeDotTaskStyles,
  REMINDER: Styles.typeDotReminderStyles,
  MEMORY: Styles.typeDotMemoryStyles,
};

interface SearchResultsCardProps {
  results: SearchResultsFieldsFragment;
  onOpenRecord: (record: SearchRecordFragment) => void;
  onSeeAll: (recordType: RecordType | null, query: string) => void;
}

/** `SearchPassport`, `SearchResults`, `SearchDegraded` (FR-7 to FR-10, FR-20). */
export const SearchResultsCard = (props: SearchResultsCardProps): ReactElement => {
  const { results, onOpenRecord, onSeeAll } = props;
  const matchCount = results.groups.reduce((sum, group) => sum + group.total, 0);
  const hasMatches = results.groups.length > 0;

  if (!hasMatches) {
    return (
      <div className={Styles.cardStyles}>
        <div className={Styles.cardHeadStyles}>
          <span className={cn(Styles.pillBaseStyles, Styles.pillMutedStyles)}>
            <Search size={12} /> No records match “{results.query}”
          </span>
        </div>
        {results.meaningUnavailable && <MeaningUnavailableStrip />}
        <div className={Styles.searchNoMatchBodyStyles}>
          {results.meaningUnavailable
            ? "Nothing you have recorded matches by word."
            : "Nothing you have recorded matches by word or by meaning."}
        </div>
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
        <span className={cn(Styles.pillBaseStyles, Styles.pillDoneStyles)}>
          <Check size={13} /> {matchCount} {matchCount === 1 ? "record matches" : "records match"} “
          {results.query}”
        </span>
      </div>
      {results.meaningUnavailable && <MeaningUnavailableStrip />}
      {results.groups.map((group, index) => (
        <SearchGroup
          key={group.recordType}
          group={group}
          isFirst={index === 0}
          query={results.query}
          onOpenRecord={onOpenRecord}
          onSeeAll={onSeeAll}
        />
      ))}
      <div className={Styles.cardFootStyles}>
        <span>Best match first · only your records are searched</span>
        <Button size="sm" onClick={() => onSeeAll(null, results.query)}>
          Open in Records <ArrowRight size={14} />
        </Button>
      </div>
    </div>
  );
};

interface SearchGroupProps {
  group: SearchGroupFragment;
  isFirst: boolean;
  query: string;
  onOpenRecord: (record: SearchRecordFragment) => void;
  onSeeAll: (recordType: RecordType | null, query: string) => void;
}

/** Design delta `.ghead` and `.hit`: one type, at most five, best first. */
const SearchGroup = (props: SearchGroupProps): ReactElement => {
  const { group, isFirst, query, onOpenRecord, onSeeAll } = props;
  const hasMore = group.total > group.hits.length;

  return (
    <div className={cn(Styles.searchGroupStyles, !isFirst && Styles.searchGroupSeparatorStyles)}>
      <div className={Styles.searchGroupHeadStyles}>
        <span className={Styles.searchGroupLabelStyles}>
          <span className={GROUP_DOT[group.recordType]} />
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
        <SearchHitRow key={hit.record.id} record={hit.record} onOpenRecord={onOpenRecord} />
      ))}
    </div>
  );
};

interface SearchHitRowProps {
  record: SearchRecordFragment;
  onOpenRecord: (record: SearchRecordFragment) => void;
}

/** FR-9: type, title, date and status, as the records table shows them. */
const SearchHitRow = (props: SearchHitRowProps): ReactElement => {
  const { record, onOpenRecord } = props;

  return (
    <div className={Styles.searchHitRowStyles} onClick={() => onOpenRecord(record)}>
      <SearchHitCells record={record} />
    </div>
  );
};

const SearchHitCells = (props: { record: SearchRecordFragment }): ReactElement => {
  const { record } = props;

  switch (record.__typename) {
    case "Task": {
      const isDone = record.status === "DONE";
      return (
        <>
          <span className={Styles.searchHitTitleStyles}>{record.title}</span>
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
          <span className={Styles.searchHitDateStyles}>{formatShortDate(record.createdAt)}</span>
          <span className={Styles.searchHitStatusStyles}>
            <CategoryTag category={record.category} />
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

/** `SearchStates`: a word search's loading card. */
export const SearchLoadingCard = (): ReactElement => (
  <div className={Styles.cardStyles}>
    <div className={Styles.cardHeadStyles}>
      <span className={cn(Styles.pillBaseStyles, Styles.pillWaitStyles)}>
        <Clock size={13} /> Searching your records…
      </span>
    </div>
    <div className="flex flex-col gap-3 px-4 py-3.5">
      <div className="h-[11px] w-[70%] animate-pulse rounded bg-border" />
      <div className="h-[11px] w-[52%] animate-pulse rounded bg-border" />
      <div className="h-[11px] w-[61%] animate-pulse rounded bg-border" />
    </div>
  </div>
);
