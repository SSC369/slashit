import { AlertCircle, LogIn, SearchX, WifiOff } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useGetExpensePeriods from "../../../../api/queries/GetExpensePeriods/useGetExpensePeriods";
import { useResponseHandler as usePeriodsResponseHandler } from "../../../../api/queries/GetExpensePeriods/responseHandler";
import useGetExpenses from "../../../../api/queries/GetExpenses/useGetExpenses";
import { useResponseHandler } from "../../../../api/queries/GetExpenses/responseHandler";
import useGetExpenseSummary from "../../../../api/queries/GetExpenseSummary/useGetExpenseSummary";
import { useResponseHandler as useSummaryResponseHandler } from "../../../../api/queries/GetExpenseSummary/responseHandler";
import { API_FAILED } from "../../../../constants/apiConstants";
import { EXPENSE_CATEGORY_LABEL } from "../../../../constants/expenseConstants";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import type { ExpensesFilterInput } from "../../../../../types.generated";
import { periodIdOf, type ExpenseCategoryFilterType } from "../../../../stores/ExpensesStore";
import { useStore } from "../../../../stores/StoreProvider";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import EmptyExpenses from "../../components/EmptyExpenses";
import ExpenseCategoryChips from "../../components/ExpenseCategoryChips";
import ExpenseSummaryBand from "../../components/ExpenseSummaryBand";
import ExpenseTable from "../../components/ExpenseTable";
import ReminderListNotice from "../../components/ReminderListNotice";
import * as RecordsStyles from "../../components/styles";
import * as Styles from "./styles";

type ListStateType =
  | "SESSION_ENDED"
  | "ERROR"
  | "LOADING"
  | "EMPTY"
  | "EMPTY_PERIOD"
  | "NO_MATCH"
  | "LIST";

const toFilterInput = (
  category: ExpenseCategoryFilterType,
  range: { start: string | null; end: string | null },
): ExpensesFilterInput => ({
  category: category === "ALL" ? null : category,
  start: range.start,
  end: range.end,
});

/**
 * The Expenses tab (FR-16 to FR-18): loads the picker's periods, then the
 * expenses and their totals for the picked period and category, and draws
 * whichever state the load is in (`RecordsExpenses`, `ExpensesStates`). The
 * picker itself sits in RecordsController's toolbar.
 */
const ExpensesController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const isOnline = useOnlineStatus();
  const periodsQuery = useGetExpensePeriods();
  const listQuery = useGetExpenses();
  const summaryQuery = useGetExpenseSummary();
  const { handleResponse: handlePeriods } = usePeriodsResponseHandler();
  const { handleResponse: handleList } = useResponseHandler();
  const { handleResponse: handleSummary } = useSummaryResponseHandler();

  const { categoryFilter, periodId } = store.expenses;
  const period = store.expenses.selectedPeriod;

  useEffect(() => {
    periodsQuery.triggerAPI({});
    // triggerAPI is left out on purpose, per repo-rules.md §13.4.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!periodsQuery.data) return;
    handlePeriods({ data: periodsQuery.data, onPeriodsLoaded: (periods) => store.expenses.setPeriods(periods) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [periodsQuery.data]);

  // The list and the band load together, for the same range (FR-28).
  useEffect(() => {
    if (period === null) return;
    const filter = toFilterInput(categoryFilter, period);
    listQuery.triggerAPI({ filter });
    summaryQuery.triggerAPI({ filter });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryFilter, periodId, period === null]);

  useEffect(() => {
    if (!listQuery.data) return;
    handleList({ data: listQuery.data, onExpensesLoaded: (expenses) => store.expenses.setExpenses(expenses) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listQuery.data]);

  useEffect(() => {
    if (!summaryQuery.data) return;
    handleSummary({ data: summaryQuery.data, onSummaryLoaded: (summary) => store.expenses.setSummary(summary) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [summaryQuery.data]);

  const expenses = store.expenses.getVisible();
  const hasSyncedOnce = store.expenses.lastSyncedAt !== null;
  const failedQuery = [periodsQuery, listQuery].find((query) => query.apiStatus === API_FAILED);
  // Offline with a list already loaded: keep showing it (`ExpensesStates`).
  const isShowingSavedCopy = !isOnline && hasSyncedOnce;
  const isAllTime = period?.key === "ALL_TIME";

  let listState: ListStateType = "LIST";
  if (failedQuery && isSessionEndedError(failedQuery.apiError)) listState = "SESSION_ENDED";
  else if (failedQuery && !isShowingSavedCopy) listState = "ERROR";
  else if (!hasSyncedOnce || period === null) listState = "LOADING";
  else if (expenses.length > 0) listState = "LIST";
  else if (categoryFilter !== "ALL") listState = "NO_MATCH";
  else listState = isAllTime ? "EMPTY" : "EMPTY_PERIOD";

  const handleRetry = (): void => {
    if (period === null) {
      periodsQuery.triggerAPI({});
      return;
    }
    const filter = toFilterInput(categoryFilter, period);
    listQuery.triggerAPI({ filter });
    summaryQuery.triggerAPI({ filter });
  };

  const chips = <ExpenseCategoryChips selected={categoryFilter} onSelect={store.expenses.setCategoryFilter} />;
  // The band shows only totals for the picked range, never another period's
  // while this one loads.
  const summary =
    store.expenses.summary !== null &&
    period !== null &&
    periodIdOf(store.expenses.summary) === periodIdOf(period)
      ? store.expenses.summary
      : null;
  const periodLabel = period?.label ?? "";

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
          onAction={handleRetry}
        />
      );
    case "EMPTY":
      return <EmptyExpenses onGoToCapture={() => navigate("/")} />;
    case "EMPTY_PERIOD":
      return (
        <>
          {chips}
          <div className={RecordsStyles.emptyPeriodStyles}>
            <div className={RecordsStyles.emptyPeriodTitleStyles}>No expenses recorded {period?.phrase}</div>
            <div className={RecordsStyles.emptyPeriodBodyStyles}>
              Totals appear once there is something to add up.
            </div>
          </div>
        </>
      );
    case "NO_MATCH":
      return (
        <>
          {chips}
          <ReminderListNotice
            icon={<SearchX size={24} />}
            title={`No ${categoryFilter === "ALL" ? "" : EXPENSE_CATEGORY_LABEL[categoryFilter]} expenses ${isAllTime ? "yet" : `in ${periodLabel}`}`}
            body="Choose All to see every expense in the period."
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
          {listState === "LIST" && summary !== null && summary.count > 0 && (
            <ExpenseSummaryBand summary={summary} />
          )}
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
