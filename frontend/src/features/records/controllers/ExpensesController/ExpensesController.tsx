import { AlertCircle, LogIn, SearchX, WifiOff } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useGetExpenses from "../../../../api/queries/GetExpenses/useGetExpenses";
import { useResponseHandler } from "../../../../api/queries/GetExpenses/responseHandler";
import { API_FAILED } from "../../../../constants/apiConstants";
import { EXPENSE_CATEGORY_LABEL } from "../../../../constants/expenseConstants";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import type { ExpensesFilterInput } from "../../../../../types.generated";
import type { ExpenseCategoryFilterType } from "../../../../stores/ExpensesStore";
import { useStore } from "../../../../stores/StoreProvider";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import EmptyExpenses from "../../components/EmptyExpenses";
import ExpenseCategoryChips from "../../components/ExpenseCategoryChips";
import ExpenseTable from "../../components/ExpenseTable";
import ReminderListNotice from "../../components/ReminderListNotice";
import * as RecordsStyles from "../../components/styles";
import * as Styles from "./styles";

type ListStateType = "SESSION_ENDED" | "ERROR" | "LOADING" | "EMPTY" | "NO_MATCH" | "LIST";

const toFilterInput = (filter: ExpenseCategoryFilterType): ExpensesFilterInput => ({
  category: filter === "ALL" ? null : filter,
});

/**
 * The Expenses tab (FR-16, FR-17's category half): loads expenses into the
 * expenses store and draws whichever state the load is in (`ExpensesStates`).
 * Rendered by RecordsController, which owns the tabs. Periods, the band and
 * search arrive with slices 2 and 3.
 */
const ExpensesController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const isOnline = useOnlineStatus();
  const { triggerAPI, data, apiStatus, apiError } = useGetExpenses();
  const { handleResponse } = useResponseHandler();

  const { categoryFilter } = store.expenses;

  useEffect(() => {
    triggerAPI({ filter: toFilterInput(categoryFilter) });
    // triggerAPI is left out on purpose, per repo-rules.md §13.4.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryFilter]);

  useEffect(() => {
    if (!data) return;
    handleResponse({ data, onExpensesLoaded: (expenses) => store.expenses.setExpenses(expenses) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const expenses = store.expenses.getVisible();
  const hasSyncedOnce = store.expenses.lastSyncedAt !== null;
  const hasFailed = apiStatus === API_FAILED;
  // Offline with a list already loaded: keep showing it (`ExpensesStates`).
  const isShowingSavedCopy = !isOnline && hasSyncedOnce;

  let listState: ListStateType = "LIST";
  if (hasFailed && isSessionEndedError(apiError)) listState = "SESSION_ENDED";
  else if (hasFailed && !isShowingSavedCopy) listState = "ERROR";
  else if (!hasSyncedOnce) listState = "LOADING";
  else if (expenses.length === 0) listState = categoryFilter === "ALL" ? "EMPTY" : "NO_MATCH";

  const chips = <ExpenseCategoryChips selected={categoryFilter} onSelect={store.expenses.setCategoryFilter} />;

  switch (listState) {
    case "SESSION_ENDED":
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Sign in to see your expenses"
          body="Your session ended. Expenses are only shown to the account that recorded them."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    case "ERROR":
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Your expenses could not be loaded"
          body="Nothing is lost. Check your connection and try again."
          actionLabel="Try again"
          onAction={() => triggerAPI({ filter: toFilterInput(categoryFilter) })}
        />
      );
    case "EMPTY":
      return <EmptyExpenses onGoToCapture={() => navigate("/")} />;
    case "NO_MATCH":
      return (
        <>
          {chips}
          <ReminderListNotice
            icon={<SearchX size={24} />}
            title={`No ${categoryFilter === "ALL" ? "" : EXPENSE_CATEGORY_LABEL[categoryFilter]} expenses`}
            body="Choose All to see every expense."
            actionLabel="Show all"
            onAction={() => store.expenses.setCategoryFilter("ALL")}
          />
        </>
      );
    case "LOADING":
    case "LIST":
      return (
        <>
          {!isOnline && (
            <div className={RecordsStyles.offlineNoteStyles} role="status">
              <WifiOff size={16} className={Styles.offlineIconStyles} />
              <span>
                <span className={RecordsStyles.offlineNoteTitleStyles}>You are offline.</span> Expenses
                already loaded stay readable. Totals refresh when you reconnect.
              </span>
            </div>
          )}
          {chips}
          <ExpenseTable
            expenses={expenses}
            isLoading={listState === "LOADING"}
            onOpenExpense={(id) => navigate(`/records/expenses/${id}`)}
          />
        </>
      );
    default: {
      const unhandled: never = listState;
      throw new Error(`Unhandled expenses list state: ${String(unhandled)}`);
    }
  }
};

export default observer(ExpensesController);
