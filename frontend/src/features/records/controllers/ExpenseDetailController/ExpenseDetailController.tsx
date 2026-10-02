import { AlertCircle, ChevronRight, FileQuestion, LogIn } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useState, type ReactElement } from "react";
import { useNavigate, useParams } from "react-router";

import useDeleteExpense from "../../../../api/mutations/DeleteExpense/useDeleteExpense";
import useUpdateExpense from "../../../../api/mutations/UpdateExpense/useUpdateExpense";
import useGetExpense from "../../../../api/queries/GetExpense/useGetExpense";
import { useResponseHandler } from "../../../../api/queries/GetExpense/responseHandler";
import PageTopbar from "../../../../components/PageTopbar";
import { API_FAILED, API_FETCHING } from "../../../../constants/apiConstants";
import type { ExpenseFieldsFragment } from "../../../../fragments/ExpenseFields.generated";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import { useStore } from "../../../../stores/StoreProvider";
import type { UpdateExpenseInput } from "../../../../../types.generated";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import { formatRupees, paiseToInput, parseRupees } from "../../../../utils/money";
import DeleteConfirmModal from "../../components/DeleteConfirmModal";
import ExpenseDetailView, { ExpenseDetailSkeleton } from "../../components/ExpenseDetailView";
import ExpenseEditForm, {
  type ExpenseDraft,
  type ExpenseEditBannerType,
  type ExpenseFieldErrors,
} from "../../components/ExpenseEditForm";
import ReminderListNotice from "../../components/ReminderListNotice";
import * as RecordsStyles from "../../components/styles";
import * as Styles from "./styles";

export type ExpenseDetailModeType = "VIEW" | "EDIT";

interface ExpenseDetailControllerProps {
  mode: ExpenseDetailModeType;
}

const NO_FIELD_ERRORS: ExpenseFieldErrors = { amount: null, description: null };

const toDraft = (expense: ExpenseFieldsFragment): ExpenseDraft => ({
  amountText: paiseToInput(expense.amountPaise),
  description: expense.description,
  category: expense.category,
  spentOn: expense.spentOn,
});

/** Only what changed: a description sent unchanged would still clear its embedding. */
const changedFields = (expense: ExpenseFieldsFragment, draft: ExpenseDraft): UpdateExpenseInput => {
  const input: UpdateExpenseInput = {};
  const amountPaise = parseRupees(draft.amountText);
  if (amountPaise !== null && amountPaise !== expense.amountPaise) input.amountPaise = amountPaise;
  const description = draft.description.trim();
  if (description !== expense.description) input.description = description;
  if (draft.category !== expense.category) input.category = draft.category;
  if (draft.spentOn !== expense.spentOn) input.spentOn = draft.spentOn;
  return input;
};

/**
 * One expense at `/records/expenses/:id` (FR-20), its edit form at `.../edit`
 * (FR-21), and Delete from the detail (FR-22).
 */
const ExpenseDetailController = (props: ExpenseDetailControllerProps): ReactElement => {
  const { mode } = props;
  const { id = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const store = useStore();
  const isOnline = useOnlineStatus();

  const [isNotFound, setIsNotFound] = useState(false);
  const [draft, setDraft] = useState<ExpenseDraft | null>(null);
  const [serverErrors, setServerErrors] = useState<ExpenseFieldErrors>(NO_FIELD_ERRORS);
  const [banner, setBanner] = useState<ExpenseEditBannerType>("NONE");
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { triggerAPI: triggerGetExpense, data, apiStatus, apiError } = useGetExpense();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: triggerUpdateExpense, apiStatus: updateApiStatus } = useUpdateExpense();
  const { triggerAPI: triggerDeleteExpense, apiStatus: deleteApiStatus } = useDeleteExpense();

  const expense = store.expenses.get(id);
  const isEditing = mode === "EDIT";
  const hasExpense = expense !== null;

  useEffect(() => {
    if (!id) return;
    setIsNotFound(false);
    triggerGetExpense({ id });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!data) return;
    handleResponse({
      data,
      onExpenseLoaded: (loaded) => store.expenses.upsert(loaded),
      onExpenseNotFound: () => setIsNotFound(true),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  // A fresh draft each time the form opens; never while it is being typed in.
  useEffect(() => {
    if (!isEditing || expense === null) {
      setDraft(null);
      return;
    }
    setDraft(toDraft(expense));
    setServerErrors(NO_FIELD_ERRORS);
    setBanner("NONE");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditing, hasExpense, id]);

  const goToExpenses = (): void => {
    store.records.setKindFilter("EXPENSES");
    navigate("/records");
  };

  const handleDraftChange = (patch: Partial<ExpenseDraft>): void => {
    setDraft((current) => (current === null ? current : { ...current, ...patch }));
    if ("amountText" in patch) setServerErrors((errors) => ({ ...errors, amount: null }));
    if ("description" in patch) setServerErrors((errors) => ({ ...errors, description: null }));
  };

  const handleSave = (): void => {
    if (draft === null || expense === null) return;
    const input = changedFields(expense, draft);
    if (Object.keys(input).length === 0) {
      navigate(`/records/expenses/${id}`);
      return;
    }
    setBanner("NONE");
    triggerUpdateExpense({
      id,
      input,
      onExpenseUpdated: (updated) => {
        store.expenses.upsert(updated);
        store.toast.show({ message: "Expense updated.", linkLabel: "View", linkTo: `/records/expenses/${updated.id}` });
        navigate(`/records/expenses/${updated.id}`);
      },
      onExpenseInvalid: ({ field, message }) =>
        setServerErrors((errors) => ({ ...errors, [field === "AMOUNT" ? "amount" : "description"]: message })),
      onExpenseNotFound: () => setBanner("GONE"),
      onRequestFailed: () => setBanner("FAILED"),
    });
  };

  const openDelete = (): void => {
    setDeleteError(null);
    setIsDeleteOpen(true);
  };

  const handleConfirmDelete = (): void => {
    setDeleteError(null);
    const deleted = (): void => {
      setIsDeleteOpen(false);
      store.expenses.remove(id);
      store.toast.show({ message: "Expense deleted. It no longer counts in any total.", linkLabel: "", linkTo: "" });
      goToExpenses();
    };
    triggerDeleteExpense({
      id,
      onExpenseDeleted: deleted,
      // Deleted from another tab first: the outcome the user asked for.
      onExpenseNotFound: deleted,
      onRequestFailed: () =>
        setDeleteError("This expense could not be deleted. It still counts in your totals. Try again."),
    });
  };

  const isSessionEnded = apiStatus === API_FAILED && isSessionEndedError(apiError);
  const hasLoadFailed = apiStatus === API_FAILED && expense === null;

  const renderBody = (): ReactElement => {
    if (isNotFound) {
      return (
        <ReminderListNotice
          icon={<FileQuestion size={24} />}
          title="This expense no longer exists"
          body="It may have been deleted in another tab."
          actionLabel="Back to Expenses"
          onAction={goToExpenses}
        />
      );
    }
    if (isSessionEnded) {
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Sign in to see your expenses"
          body="Your session ended. Expenses are only shown to the account that recorded them."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    }
    if (hasLoadFailed) {
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Couldn't load this expense"
          body="Nothing is lost. Check your connection and try again."
          actionLabel="Try again"
          onAction={() => triggerGetExpense({ id })}
        />
      );
    }
    if (expense === null) return <ExpenseDetailSkeleton />;
    if (isEditing && draft !== null) {
      return (
        <ExpenseEditForm
          draft={draft}
          serverErrors={serverErrors}
          banner={banner}
          isSaving={updateApiStatus === API_FETCHING}
          isOffline={!isOnline}
          onChange={handleDraftChange}
          onSave={handleSave}
          onCancel={() => (banner === "GONE" ? goToExpenses() : navigate(`/records/expenses/${id}`))}
        />
      );
    }
    return (
      <ExpenseDetailView
        expense={expense}
        isOffline={!isOnline}
        onEdit={() => navigate(`/records/expenses/${id}/edit`)}
        onDelete={openDelete}
      />
    );
  };

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar title="Records" />
      <div className={Styles.paneStyles}>
        <div className={isEditing ? Styles.editContentStyles : Styles.contentStyles}>
          <div className={RecordsStyles.breadcrumbStyles}>
            <span className={Styles.breadcrumbLinkStyles} onClick={() => navigate("/records")}>
              Records
            </span>
            <ChevronRight size={13} />
            <span className={Styles.breadcrumbLinkStyles} onClick={goToExpenses}>
              Expenses
            </span>
            {expense !== null && (
              <>
                <ChevronRight size={13} />
                <span className={RecordsStyles.breadcrumbCurrentStyles}>{expense.description}</span>
                {isEditing && (
                  <>
                    <ChevronRight size={13} />
                    <span className={RecordsStyles.breadcrumbCurrentStyles}>Editing</span>
                  </>
                )}
              </>
            )}
          </div>
          {renderBody()}
        </div>
      </div>

      {isDeleteOpen && expense !== null && (
        <DeleteConfirmModal
          title="Delete this expense?"
          message={
            <>
              <span className={RecordsStyles.modalTaskNameStyles}>
                {formatRupees(expense.amountPaise)} · {expense.description}
              </span>{" "}
              will be removed from your records and from every total.
            </>
          }
          confirmLabel="Delete expense"
          isBusy={deleteApiStatus === API_FETCHING}
          errorMessage={deleteError}
          onCancel={() => setIsDeleteOpen(false)}
          onConfirm={handleConfirmDelete}
        />
      )}
    </div>
  );
};

export default observer(ExpenseDetailController);
