import { AlertCircle, AlertTriangle, LogIn, SearchX, WifiOff } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useRef, useState, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useRecordSearchEvent from "../../../../api/mutations/RecordSearchEvent/useRecordSearchEvent";
import { useResponseHandler } from "../../../../api/queries/SearchRecords/responseHandler";
import useSearchRecords from "../../../../api/queries/SearchRecords/useSearchRecords";
import { API_FAILED } from "../../../../constants/apiConstants";
import Button from "../../../../design-system/components/Button";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import type { MemoryCategoryFilterType } from "../../../../stores/MemoriesStore";
import type { RecordRow, RecordsKindFilter } from "../../../../stores/RecordsStore";
import { useStore } from "../../../../stores/StoreProvider";
import { recordPath } from "../../../../utils/recordPath";
import type { RecordType } from "../../../../../types.generated";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import CategoryChips from "../../components/CategoryChips";
import RecordTable from "../../components/RecordTable";
import ReminderListNotice from "../../components/ReminderListNotice";
import * as RecordsStyles from "../../components/styles";

const SEARCH_DEBOUNCE_MS = 250;
const PAGE_SIZE = 50;

const TAB_RECORD_TYPE: Record<RecordsKindFilter, RecordType | null> = {
  ALL: null,
  TASKS: "TASK",
  REMINDERS: "REMINDER",
  MEMORIES: "MEMORY",
  // Unreachable until slice 2 (FR-30): the Events tab does not search yet.
  EVENTS: null,
};

const TAB_NOUN: Record<RecordsKindFilter, string> = {
  ALL: "records",
  TASKS: "tasks",
  REMINDERS: "reminders",
  MEMORIES: "memories",
  EVENTS: "events",
};

type SearchStateType =
  | "OFFLINE"
  | "SESSION_ENDED"
  | "ERROR"
  | "TOO_LONG"
  | "LOADING"
  | "FILTERED_NO_MATCH"
  | "CATEGORY_NO_MATCH"
  | "NO_MATCH"
  | "LIST";

const matchesCategory = (row: RecordRow, filter: MemoryCategoryFilterType): boolean => {
  if (row.kind !== "MEMORY" || filter === "ALL") return true;
  if (filter === "UNCATEGORISED") return row.memory.category === null;
  return row.memory.category === filter;
};

/**
 * Epic 005, FR-22 to FR-24: the records view while its box holds text. The
 * same matching and ranking as `/search`, for whichever tab is open, drawn
 * as `RecordsSearch` and `RecordsSearchStates`. Rendered by RecordsController.
 */
const RecordsSearchController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const isOnline = useOnlineStatus();
  const { triggerAPI, data, apiStatus, apiError } = useSearchRecords();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: recordSearchEvent } = useRecordSearchEvent();
  const [tooLongLength, setTooLongLength] = useState<number | null>(null);
  // Which page the latest request asked for, so its response is placed right.
  const lastRequest = useRef({ key: "", offset: 0 });

  const { kindFilter, searchSortMode } = store.records;
  const trimmedSearch = store.records.searchText.trim();
  const recordType = TAB_RECORD_TYPE[kindFilter];
  const currentKey = `${trimmedSearch}|${recordType ?? "ALL"}`;
  const { categoryFilter } = store.memories;

  const requestPage = (offset: number): void => {
    lastRequest.current = { key: currentKey, offset };
    triggerAPI({ text: trimmedSearch, recordType, offset, limit: PAGE_SIZE });
  };

  useEffect(() => {
    setTooLongLength(null);
    const timeoutId = window.setTimeout(() => requestPage(0), SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timeoutId);
    // requestPage is left out on purpose, per repo-rules.md §13.4.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentKey]);

  useEffect(() => {
    if (!data) return;
    handleResponse({
      data,
      onPageLoaded: (page) =>
        store.records.applySearchPage({
          key: lastRequest.current.key,
          offset: lastRequest.current.offset,
          page,
        }),
      onTooLong: (length) => setTooLongLength(length),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const rows = store.records
    .getSearchVisible()
    .filter((row) => kindFilter !== "MEMORIES" || matchesCategory(row, categoryFilter));
  const isCurrent = store.records.searchLoadedKey === currentKey;
  const hasFailed = apiStatus === API_FAILED;
  const noun = TAB_NOUN[kindFilter];

  let searchState: SearchStateType = "LIST";
  if (!isOnline && !isCurrent) searchState = "OFFLINE";
  else if (hasFailed && isSessionEndedError(apiError)) searchState = "SESSION_ENDED";
  else if (hasFailed) searchState = "ERROR";
  else if (tooLongLength !== null) searchState = "TOO_LONG";
  else if (!isCurrent) searchState = "LOADING";
  else if (rows.length === 0 && store.records.searchRefs.length > 0)
    searchState = "CATEGORY_NO_MATCH";
  else if (rows.length === 0 && kindFilter !== "ALL" && store.records.searchOtherTypesTotal > 0)
    searchState = "FILTERED_NO_MATCH";
  else if (rows.length === 0) searchState = "NO_MATCH";

  const handleOpenRow = (row: RecordRow): void => {
    recordSearchEvent({ kind: "SEARCH_RESULT_OPENED", position: rows.indexOf(row) + 1 });
    navigate(recordPath(row));
  };

  const chips =
    kindFilter === "MEMORIES" ? (
      <CategoryChips selected={categoryFilter} onSelect={store.memories.setCategoryFilter} />
    ) : null;

  switch (searchState) {
    case "OFFLINE":
      return (
        <div className={RecordsStyles.offlineNoteStyles} role="status">
          <WifiOff size={16} className="mt-0.5 shrink-0 text-command" />
          <span>
            <span className={RecordsStyles.offlineNoteTitleStyles}>You are offline.</span> Search
            needs a connection. Records already on this device stay readable.
          </span>
        </div>
      );
    case "SESSION_ENDED":
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Sign in to search your records."
          body="Your session ended."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    case "ERROR":
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Search could not run."
          body="Nothing is lost. Check your connection and try again."
          actionLabel="Try again"
          onAction={() => requestPage(0)}
        />
      );
    case "TOO_LONG":
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title={`That is ${tooLongLength ?? 0} characters.`}
          body="A search can be up to 500. Shorten it to search."
          actionLabel="Clear search"
          onAction={() => store.records.setSearchText("")}
        />
      );
    case "FILTERED_NO_MATCH": {
      const others = store.records.searchOtherTypesTotal;
      return (
        <>
          {chips}
          <ReminderListNotice
            icon={<SearchX size={24} />}
            title={`No ${noun} match “${trimmedSearch}”`}
            body={`${others} other ${others === 1 ? "record matches" : "records match"}. Choose All to see them.`}
            actionLabel="Show all"
            onAction={() => store.records.setKindFilter("ALL")}
          />
        </>
      );
    }
    case "CATEGORY_NO_MATCH":
      return (
        <>
          {chips}
          <ReminderListNotice
            icon={<SearchX size={24} />}
            title={`No memories in this category match “${trimmedSearch}”`}
            body="Choose All to see every match."
            actionLabel="Show all"
            onAction={() => store.memories.setCategoryFilter("ALL")}
          />
        </>
      );
    case "NO_MATCH":
      return (
        <>
          {chips}
          <ReminderListNotice
            icon={<SearchX size={24} />}
            title={`No ${noun} match “${trimmedSearch}”`}
            body={
              store.records.searchMeaningUnavailable
                ? "Nothing matches by word. Clear the search to see every record."
                : "Nothing matches by word or by meaning. Clear the search to see every record."
            }
            actionLabel="Clear search"
            onAction={() => store.records.setSearchText("")}
          />
        </>
      );
    case "LOADING":
    case "LIST": {
      const total = store.records.searchTotal;
      const canShowMore = store.records.searchRefs.length < total;
      return (
        <>
          {chips}
          {searchState === "LIST" && store.records.searchMeaningUnavailable && (
            <div className={RecordsStyles.searchStripStyles} role="status">
              <AlertTriangle size={14} className="shrink-0" />
              <span>Showing word matches only. Results may be incomplete.</span>
            </div>
          )}
          <RecordTable
            records={rows}
            isLoading={searchState === "LOADING"}
            onOpenRecord={handleOpenRow}
            footLeft={`${total} ${total === 1 ? "record matches" : "records match"} “${trimmedSearch}” · ${
              searchSortMode === "BEST_MATCH" ? "best match first" : "newest first"
            }`}
            footRight={
              <>
                Same matching as <span className={RecordsStyles.searchFootNoteStyles}>/search</span>
              </>
            }
            afterRows={
              canShowMore ? (
                <div className={RecordsStyles.showMoreRowStyles}>
                  <Button size="sm" onClick={() => requestPage(store.records.searchRefs.length)}>
                    Show more
                  </Button>
                </div>
              ) : null
            }
          />
        </>
      );
    }
    default: {
      const unhandled: never = searchState;
      throw new Error(`Unhandled records search state: ${String(unhandled)}`);
    }
  }
};

export default observer(RecordsSearchController);
