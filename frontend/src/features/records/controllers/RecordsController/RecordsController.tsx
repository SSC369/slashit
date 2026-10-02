import { ArrowUpDown, ClipboardList } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useState, type ChangeEvent, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useGetRecords from "../../../../api/queries/GetRecords/useGetRecords";
import { useResponseHandler } from "../../../../api/queries/GetRecords/responseHandler";
import useRecordsViewOpened from "../../../../api/mutations/RecordsViewOpened/useRecordsViewOpened";
import { API_SUCCESS } from "../../../../constants/apiConstants";
import Button from "../../../../design-system/components/Button";
import { cn } from "../../../../utils/cn";
import { useStore } from "../../../../stores/StoreProvider";
import { recordPath } from "../../../../utils/recordPath";
import type { RecordRow, RecordsKindFilter } from "../../../../stores/RecordsStore";
import PageTopbar from "../../../../components/PageTopbar";
import EmptyRecords from "../../components/EmptyRecords";
import ReminderListNotice from "../../components/ReminderListNotice";
import RecordTable from "../../components/RecordTable";
import * as RecordsStyles from "../../components/styles";
import EventsController from "../EventsController/EventsController";
import MemoriesController from "../MemoriesController/MemoriesController";
import RecordsSearchController from "../RecordsSearchController/RecordsSearchController";
import RemindersController from "../RemindersController/RemindersController";
import * as Styles from "./styles";

// FR-3's limit, shared with `/search`: the box stops at the length a search allows.
const MAX_SEARCH_LENGTH = 500;

const TABS: { filter: RecordsKindFilter; label: string }[] = [
  { filter: "ALL", label: "All" },
  { filter: "TASKS", label: "Tasks" },
  { filter: "REMINDERS", label: "Reminders" },
  { filter: "MEMORIES", label: "Memories" },
  { filter: "EVENTS", label: "Events" },
];

interface RecordsControllerProps {
  /** `/records/events` opens on the Events tab. */
  initialKindFilter?: RecordsKindFilter;
}

const RecordsController = (props: RecordsControllerProps): ReactElement => {
  const { initialKindFilter } = props;
  const store = useStore();
  const navigate = useNavigate();
  const { triggerAPI, data, apiStatus } = useGetRecords();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: triggerRecordsViewOpened } = useRecordsViewOpened();

  const { kindFilter, searchText, sortField, searchSortMode } = store.records;
  const trimmedSearch = searchText.trim();
  const isEventsTab = kindFilter === "EVENTS";
  // Epic 005, FR-22: any text in the box moves every tab onto search's own
  // matching; the tab lists below serve only the unsearched view. Events are
  // not searchable until epic 007's slice 2 (FR-30), so their tab ignores it.
  const isSearching = trimmedSearch !== "" && !isEventsTab;

  useEffect(() => {
    if (initialKindFilter !== undefined) store.records.setKindFilter(initialKindFilter);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialKindFilter]);

  useEffect(() => {
    // PRD section 8's "weekly actives opening a records view" metric. Fired
    // once per mount, not per filter change, so it reflects an open, not a
    // refetch.
    triggerRecordsViewOpened();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isRemindersTab = kindFilter === "REMINDERS";
  const isMemoriesTab = kindFilter === "MEMORIES";
  // These tabs load their own queries; the records query serves All and Tasks.
  const hasOwnQuery = isRemindersTab || isMemoriesTab || isEventsTab;

  // A tab, search or sort change makes the current `apiStatus` stale until a
  // response for the new filter lands. Without this, switching tabs shows a
  // false "0 records" flash: `apiStatus` is still SUCCESS from the previous
  // tab, and `getVisible()` already returns nothing for the new one. Setting
  // state during render (React's documented pattern for resetting state when
  // a derived value changes) catches the change before the first paint, so
  // there is no flash to begin with.
  const currentFilterKey = `${kindFilter}|${sortField}`;
  const [committedFilterKey, setCommittedFilterKey] = useState(currentFilterKey);
  const [isFilterPending, setIsFilterPending] = useState(false);
  if (committedFilterKey !== currentFilterKey) {
    setCommittedFilterKey(currentFilterKey);
    setIsFilterPending(true);
  }

  useEffect(() => {
    // The Reminders and Memories tabs load their own queries, and a search
    // loads through RecordsSearchController.
    if (hasOwnQuery || isSearching) return;
    const timeoutId = window.setTimeout(() => {
      triggerAPI({
        filter: {
          kind: kindFilter,
          sortBy: sortField,
          sortDesc: false,
        },
      });
      // triggerAPI is stable across renders (it comes from a hook whose
      // identity is not tracked here on purpose, per repo-rules.md §13.4).
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, 250);
    return () => window.clearTimeout(timeoutId);
  }, [kindFilter, sortField, isSearching]);

  // A refetch whose result equals the last one keeps the same `data` object,
  // so the effect below never fires and the table would stay on its skeleton
  // (Reminders or Memories tab, then back to All). The request's own
  // LOADING-to-SUCCESS change ends the pending state instead.
  useEffect(() => {
    if (apiStatus === API_SUCCESS) setIsFilterPending(false);
  }, [apiStatus]);

  useEffect(() => {
    if (!data) return;
    handleResponse({
      data,
      onRecordsLoaded: (records) => store.records.setRecords(records),
    });
    setIsFilterPending(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const handleTabClick = (filter: RecordsKindFilter): void => {
    store.records.setKindFilter(filter);
  };

  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>): void => {
    store.records.setSearchText(event.target.value);
  };

  const handleOpenRecord = (row: RecordRow): void => {
    navigate(recordPath(row));
  };

  const records = store.records.getVisible();
  const hasLoadedOnce = apiStatus === API_SUCCESS && !isFilterPending;
  const isTrulyEmpty = hasLoadedOnce && records.length === 0 && !isSearching;

  // The very first time this account has anything at all, on the All tab,
  // the whole tab bar is hidden too: there is nothing yet to filter.
  const showFirstEverEmpty = isTrulyEmpty && kindFilter === "ALL";

  const handleToggleSearchSort = (): void => {
    store.records.setSearchSortMode(searchSortMode === "BEST_MATCH" ? "DATE" : "BEST_MATCH");
  };

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar title="Records" />

      {showFirstEverEmpty ? (
        <EmptyRecords onStartCapturing={() => navigate("/")} />
      ) : (
        <div className={RecordsStyles.paneStyles}>
          <div className={RecordsStyles.toolbarStyles}>
            <div className={RecordsStyles.tabsStyles}>
              {TABS.map((tab) => (
                <button
                  key={tab.filter}
                  type="button"
                  className={cn(
                    RecordsStyles.tabStyles,
                    kindFilter === tab.filter && RecordsStyles.tabOnStyles,
                  )}
                  onClick={() => handleTabClick(tab.filter)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div className={RecordsStyles.toolbarRightStyles}>
              {!isEventsTab && (
                <div className={RecordsStyles.searchBoxStyles}>
                  <input
                    className={RecordsStyles.searchInputStyles}
                    type="text"
                    placeholder={isMemoriesTab ? "Search memories" : "Search records"}
                    value={searchText}
                    maxLength={MAX_SEARCH_LENGTH}
                    onChange={handleSearchChange}
                  />
                </div>
              )}
              {isSearching && (
                <Button size="sm" onClick={handleToggleSearchSort}>
                  <ArrowUpDown size={14} />
                  {searchSortMode === "BEST_MATCH" ? "Sorted by best match" : "Sorted by date"}
                </Button>
              )}
            </div>
          </div>
          {isSearching ? (
            <RecordsSearchController />
          ) : isRemindersTab ? (
            <RemindersController />
          ) : isMemoriesTab ? (
            <MemoriesController />
          ) : isEventsTab ? (
            <EventsController />
          ) : isTrulyEmpty ? (
            <ReminderListNotice
              icon={<ClipboardList size={24} />}
              title="No tasks yet"
              body="Tasks appear here the moment you add one. Nothing is hidden from this view."
              actionLabel="Start capturing"
              onAction={() => navigate("/")}
            />
          ) : (
            <RecordTable records={records} onOpenRecord={handleOpenRecord} isLoading={!hasLoadedOnce} />
          )}
        </div>
      )}
    </div>
  );
};

export default observer(RecordsController);
