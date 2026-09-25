import { AlertCircle, Bookmark, LogIn, SearchX } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useGetMemories from "../../../../api/queries/GetMemories/useGetMemories";
import { useResponseHandler } from "../../../../api/queries/GetMemories/responseHandler";
import { API_FAILED } from "../../../../constants/apiConstants";
import { CATEGORY_LABEL } from "../../../../constants/memoryConstants";
import type { MemoriesFilterInput } from "../../../../../types.generated";
import type { MemoryCategoryFilterType } from "../../../../stores/MemoriesStore";
import { useStore } from "../../../../stores/StoreProvider";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import CategoryChips from "../../components/CategoryChips";
import MemoryTable from "../../components/MemoryTable";
import ReminderListNotice from "../../components/ReminderListNotice";

const SEARCH_DEBOUNCE_MS = 250;

type ListStateType = "SESSION_ENDED" | "ERROR" | "LOADING" | "EMPTY" | "NO_MATCH" | "LIST";

const toFilterInput = (filter: MemoryCategoryFilterType, search: string): MemoriesFilterInput => ({
  category: filter === "ALL" || filter === "UNCATEGORISED" ? null : filter,
  uncategorised: filter === "UNCATEGORISED",
  search: search || null,
});

const describeFilter = (filter: MemoryCategoryFilterType): string => {
  if (filter === "UNCATEGORISED") return "without a category";
  if (filter === "ALL") return "";
  return `in ${CATEGORY_LABEL[filter]}`;
};

/**
 * The Memories tab (FR-15, FR-16): loads memories into the memories store and
 * draws whichever state the load is in (`MemoriesStates`). Rendered by
 * RecordsController, which owns the tabs and the shared search box.
 */
const MemoriesController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const { triggerAPI, data, apiStatus, apiError } = useGetMemories();
  const { handleResponse } = useResponseHandler();

  const { categoryFilter } = store.memories;
  const trimmedSearch = store.records.searchText.trim();

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      triggerAPI({ filter: toFilterInput(categoryFilter, trimmedSearch) });
      // triggerAPI is left out on purpose, per repo-rules.md §13.4.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timeoutId);
  }, [categoryFilter, trimmedSearch]);

  useEffect(() => {
    if (!data) return;
    handleResponse({ data, onMemoriesLoaded: (memories) => store.memories.setMemories(memories) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const memories = store.memories.getVisible();
  const hasSyncedOnce = store.memories.lastSyncedAt !== null;
  const hasFailed = apiStatus === API_FAILED;
  const isFiltered = categoryFilter !== "ALL" || trimmedSearch !== "";

  let listState: ListStateType = "LIST";
  if (hasFailed && isSessionEndedError(apiError)) listState = "SESSION_ENDED";
  else if (hasFailed) listState = "ERROR";
  else if (!hasSyncedOnce) listState = "LOADING";
  else if (memories.length === 0) listState = isFiltered ? "NO_MATCH" : "EMPTY";

  const handleRetry = (): void => {
    triggerAPI({ filter: toFilterInput(categoryFilter, trimmedSearch) });
  };

  const handleClearFilters = (): void => {
    store.memories.setCategoryFilter("ALL");
    store.records.setSearchText("");
  };

  const chips = (
    <CategoryChips selected={categoryFilter} onSelect={store.memories.setCategoryFilter} />
  );

  switch (listState) {
    case "SESSION_ENDED":
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Sign in to see your memories"
          body="Your session ended. Memories are only ever shown to the account that saved them."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    case "ERROR":
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Your memories could not be loaded"
          body="Nothing is lost. Check your connection and try again."
          actionLabel="Try again"
          onAction={handleRetry}
        />
      );
    case "EMPTY":
      return (
        <ReminderListNotice
          icon={<Bookmark size={24} />}
          title="Nothing remembered yet"
          body="Save a fact with /remember and it appears here. For example: /remember My passport expires in 2030"
          actionLabel="Go to Capture"
          onAction={() => navigate("/")}
        />
      );
    case "NO_MATCH":
      return (
        <>
          {chips}
          <ReminderListNotice
            icon={<SearchX size={24} />}
            title={
              trimmedSearch
                ? `No memories match “${trimmedSearch}” ${describeFilter(categoryFilter)}`.trim()
                : `No memories ${describeFilter(categoryFilter)}`
            }
            body="Choose All to see every memory."
            actionLabel="Show all"
            onAction={handleClearFilters}
          />
        </>
      );
    case "LOADING":
    case "LIST":
      return (
        <>
          {chips}
          <MemoryTable
            memories={memories}
            isLoading={listState === "LOADING"}
            onOpenMemory={(id) => navigate(`/records/memories/${id}`)}
          />
        </>
      );
    default: {
      const unhandled: never = listState;
      throw new Error(`Unhandled memories list state: ${String(unhandled)}`);
    }
  }
};

export default observer(MemoriesController);
