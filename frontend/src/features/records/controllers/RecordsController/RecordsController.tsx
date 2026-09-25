import { observer } from "mobx-react-lite";
import { useEffect, type ChangeEvent, type ReactElement } from "react";
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
import RecordTable from "../../components/RecordTable";
import * as RecordsStyles from "../../components/styles";
import MemoriesController from "../MemoriesController/MemoriesController";
import RemindersController from "../RemindersController/RemindersController";
import * as Styles from "./styles";

const TABS: { filter: RecordsKindFilter; label: string }[] = [
  { filter: "ALL", label: "All" },
  { filter: "TASKS", label: "Tasks" },
  { filter: "REMINDERS", label: "Reminders" },
  { filter: "MEMORIES", label: "Memories" },
];

const RecordsController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const { triggerAPI, data, apiStatus } = useGetRecords();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: triggerRecordsViewOpened } = useRecordsViewOpened();

  const { kindFilter, searchText, sortField } = store.records;

  useEffect(() => {
    // PRD section 8's "weekly actives opening a records view" metric. Fired
    // once per mount, not per filter change, so it reflects an open, not a
    // refetch.
    triggerRecordsViewOpened();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isRemindersTab = kindFilter === "REMINDERS";
  const isMemoriesTab = kindFilter === "MEMORIES";
  // Both tabs load their own queries; the records query serves All and Tasks.
  const hasOwnQuery = isRemindersTab || isMemoriesTab;

  useEffect(() => {
    // The Reminders and Memories tabs load their own queries.
    if (hasOwnQuery) return;
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
    if (row.kind === "MEMORY") {
      navigate(`/records/memories/${row.memory.id}`);
      return;
    }
    navigate(`/records/${row.task.id}`);
  };

  const records = store.records.getVisible();
  const hasLoadedOnce = apiStatus === API_SUCCESS;
  const showEmpty =
    hasLoadedOnce && records.length === 0 && !searchText && kindFilter === "ALL";

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar title="Records" />

      {showEmpty ? (
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
              <div className={RecordsStyles.searchBoxStyles}>
                <input
                  className={RecordsStyles.searchInputStyles}
                  type="text"
                  placeholder={isMemoriesTab ? "Search memories" : "Search records"}
                  value={searchText}
                  onChange={handleSearchChange}
                />
              </div>
            </div>
          </div>
          {isRemindersTab && <RemindersController />}
          {isMemoriesTab && <MemoriesController />}
          {!hasOwnQuery && (
            <RecordTable
              records={records}
              onOpenRecord={handleOpenRecord}
              isLoading={!hasLoadedOnce}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default observer(RecordsController);
