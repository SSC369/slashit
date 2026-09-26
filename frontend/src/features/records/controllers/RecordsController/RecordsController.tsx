import { ClipboardList, SearchX } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useState, type ChangeEvent, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useGetRecords from "../../../../api/queries/GetRecords/useGetRecords";
import { useResponseHandler } from "../../../../api/queries/GetRecords/responseHandler";
import useRecordsViewOpened from "../../../../api/mutations/RecordsViewOpened/useRecordsViewOpened";
import { API_SUCCESS } from "../../../../constants/apiConstants";
import { cn } from "../../../../utils/cn";
import { useStore } from "../../../../stores/StoreProvider";
import type { RecordRow, RecordsKindFilter } from "../../../../stores/RecordsStore";
import PageTopbar from "../../../../components/PageTopbar";
import EmptyRecords from "../../components/EmptyRecords";
import ReminderListNotice from "../../components/ReminderListNotice";
import RecordTable from "../../components/RecordTable";
import * as RecordsStyles from "../../components/styles";
import RemindersController from "../RemindersController/RemindersController";
import * as Styles from "./styles";

const TABS: { filter: RecordsKindFilter; label: string }[] = [
  { filter: "ALL", label: "All" },
  { filter: "TASKS", label: "Tasks" },
  { filter: "REMINDERS", label: "Reminders" },
];

const RecordsController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const { triggerAPI, data, apiStatus } = useGetRecords();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: triggerRecordsViewOpened } = useRecordsViewOpened();

  const { kindFilter, searchText, sortField } = store.records;
  const trimmedSearch = searchText.trim();

  useEffect(() => {
    // PRD section 8's "weekly actives opening a records view" metric. Fired
    // once per mount, not per filter change, so it reflects an open, not a
    // refetch.
    triggerRecordsViewOpened();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isRemindersTab = kindFilter === "REMINDERS";

  // A tab, search or sort change makes the current `apiStatus` stale until a
  // response for the new filter lands. Without this, switching tabs shows a
  // false "0 records" flash: `apiStatus` is still SUCCESS from the previous
  // tab, and `getVisible()` already returns nothing for the new one. Setting
  // state during render (React's documented pattern for resetting state when
  // a derived value changes) catches the change before the first paint, so
  // there is no flash to begin with.
  const currentFilterKey = `${kindFilter}|${searchText}|${sortField}`;
  const [committedFilterKey, setCommittedFilterKey] = useState(currentFilterKey);
  const [isFilterPending, setIsFilterPending] = useState(false);
  if (committedFilterKey !== currentFilterKey) {
    setCommittedFilterKey(currentFilterKey);
    setIsFilterPending(true);
  }

  useEffect(() => {
    // The Reminders tab loads its own grouped query.
    if (isRemindersTab) return;
    const timeoutId = window.setTimeout(() => {
      triggerAPI({
        filter: {
          kind: kindFilter,
          search: searchText || null,
          sortBy: sortField,
          sortDesc: false,
        },
      });
      // triggerAPI is stable across renders (it comes from a hook whose
      // identity is not tracked here on purpose, per repo-rules.md §13.4).
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, 250);
    return () => window.clearTimeout(timeoutId);
  }, [kindFilter, searchText, sortField]);

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
    if (row.kind === "REMINDER") {
      navigate(`/records/reminders/${row.reminder.id}`);
      return;
    }
    navigate(`/records/${row.task.id}`);
  };

  const records = store.records.getVisible();
  const hasLoadedOnce = apiStatus === API_SUCCESS && !isFilterPending;
  const isTrulyEmpty = hasLoadedOnce && records.length === 0 && !trimmedSearch;
  const isNoMatch = hasLoadedOnce && records.length === 0 && trimmedSearch !== "";
  const noun = kindFilter === "TASKS" ? "tasks" : "records";

  // The very first time this account has anything at all, on the All tab,
  // the whole tab bar is hidden too: there is nothing yet to filter.
  const showFirstEverEmpty = isTrulyEmpty && kindFilter === "ALL";

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
              <span className={RecordsStyles.tabHintStyles}>More types arrive with later epics</span>
            </div>
            <div className={RecordsStyles.toolbarRightStyles}>
              <div className={RecordsStyles.searchBoxStyles}>
                <input
                  className={RecordsStyles.searchInputStyles}
                  type="text"
                  placeholder="Search records"
                  value={searchText}
                  onChange={handleSearchChange}
                />
              </div>
            </div>
          </div>
          {isRemindersTab ? (
            <RemindersController />
          ) : isNoMatch ? (
            <ReminderListNotice
              icon={<SearchX size={24} />}
              title={`No ${noun} match “${trimmedSearch}”`}
              body="Search covers the title. Try another word, or clear the search."
              actionLabel="Clear search"
              onAction={() => store.records.setSearchText("")}
            />
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
