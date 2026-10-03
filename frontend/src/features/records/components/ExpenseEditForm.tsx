import { Calendar } from "lucide-react";
import { useState, type ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import DatePicker from "../../../components/DatePicker";
import Button from "../../../design-system/components/Button";
import {
  EXPENSE_CATEGORIES,
  EXPENSE_CATEGORY_LABEL,
  MAX_DESCRIPTION_LENGTH,
} from "../../../constants/expenseConstants";
import type { ExpenseCategory } from "../../../../types.generated";
import { cn } from "../../../utils/cn";
import { formatDayShortWithYear, todayIso } from "../../../utils/localDate";
import { parseRupees } from "../../../utils/money";
import * as Styles from "./styles";

export interface ExpenseDraft {
  /** As typed: "850", "1,200.50". Read by `parseRupees` on save. */
  amountText: string;
  description: string;
  category: ExpenseCategory;
  spentOn: string;
}

/** A server refusal the fields cannot show. */
export type ExpenseEditBannerType = "NONE" | "FAILED" | "GONE";

export interface ExpenseFieldErrors {
  amount: string | null;
  description: string | null;
}

interface ExpenseEditFormProps {
  draft: ExpenseDraft;
  /** From the server's ExpenseInvalid; cleared when the field changes. */
  serverErrors: ExpenseFieldErrors;
  banner: ExpenseEditBannerType;
  isSaving: boolean;
  isOffline: boolean;
  onChange: (patch: Partial<ExpenseDraft>) => void;
  onSave: () => void;
  onCancel: () => void;
}

const AMOUNT_ERROR = "Enter an amount above ₹0, such as 850 or 1,200.50.";

/** `ExpenseEdit` and `DetailStates` (FR-21): any field, any date. */
const ExpenseEditForm = (props: ExpenseEditFormProps): ReactElement => {
  const { draft, serverErrors, banner, isSaving, isOffline, onChange, onSave, onCancel } = props;
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  // In characters, as the server counts (FR-13): `"😀".length` is 2 UTF-16
  // units but one character (dev log E-4).
  const descriptionLength = [...draft.description.trim()].length;
  const isAmountValid = parseRupees(draft.amountText) !== null;
  const isOverLimit = descriptionLength > MAX_DESCRIPTION_LENGTH;
  const amountError = draft.amountText.trim() !== "" && !isAmountValid ? AMOUNT_ERROR : serverErrors.amount;
  const descriptionError = isOverLimit
    ? `That is ${descriptionLength} characters. A description can be up to ${MAX_DESCRIPTION_LENGTH}.`
    : serverErrors.description;
  const canSave = isAmountValid && descriptionLength > 0 && !isOverLimit && !isOffline && banner !== "GONE";

  return (
    <>
      {banner === "FAILED" && (
        <div className={Styles.bannerErrorStyles} role="alert">
          <div>
            <div className={Styles.bannerTitleStyles}>Your changes could not be saved</div>
            <div className={Styles.bannerBodyStyles}>Nothing was changed. Your edits are still in the form.</div>
          </div>
        </div>
      )}
      {banner === "GONE" && (
        <div className={Styles.bannerWarnStyles} role="alert">
          <div>
            <div className={Styles.bannerTitleStyles}>This expense no longer exists</div>
            <div className={Styles.bannerBodyStyles}>It may have been deleted in another tab.</div>
          </div>
        </div>
      )}
      <div className={Styles.expenseEditGridStyles}>
        <div className={Styles.formRowStyles}>
          <label htmlFor="expense-amount" className={Styles.formLabelStyles}>
            Amount
          </label>
          <div className={cn(Styles.controlStyles, amountError !== null && Styles.expenseControlErrorStyles)}>
            <span className={Styles.amountControlPrefixStyles}>₹</span>
            <input
              id="expense-amount"
              className={Styles.amountControlInputStyles}
              type="text"
              inputMode="decimal"
              value={draft.amountText}
              aria-invalid={amountError !== null}
              onChange={(event) => onChange({ amountText: event.target.value })}
            />
          </div>
        </div>
        <div className={Styles.formRowStyles}>
          <label htmlFor="expense-description" className={Styles.formLabelStyles}>
            Description
          </label>
          <div className={cn(Styles.controlStyles, descriptionError !== null && Styles.expenseControlErrorStyles)}>
            <input
              id="expense-description"
              className={Styles.controlNativeInputStyles}
              type="text"
              value={draft.description}
              aria-invalid={descriptionError !== null}
              aria-describedby="expense-description-counter"
              onChange={(event) => onChange({ description: event.target.value })}
            />
          </div>
          <div
            id="expense-description-counter"
            className={cn(Styles.counterStyles, isOverLimit && Styles.counterOverStyles)}
          >
            {descriptionLength} / {MAX_DESCRIPTION_LENGTH}
          </div>
        </div>
      </div>
      {(amountError !== null || descriptionError !== null) && (
        <div className={Styles.expenseEditErrorsStyles}>
          {amountError !== null && <div className={Styles.fieldErrorStyles}>{amountError}</div>}
          {descriptionError !== null && <div className={Styles.fieldErrorStyles}>{descriptionError}</div>}
        </div>
      )}
      <div className={Styles.formRowStyles}>
        <span className={Styles.formLabelStyles}>Category</span>
        <div className={Styles.segStyles} role="radiogroup" aria-label="Category">
          {EXPENSE_CATEGORIES.map((category) => (
            <button
              key={category}
              type="button"
              role="radio"
              aria-checked={draft.category === category}
              className={cn(Styles.segOptionStyles, draft.category === category && Styles.segOptionOnStyles)}
              onClick={() => onChange({ category })}
            >
              {EXPENSE_CATEGORY_LABEL[category]}
            </button>
          ))}
        </div>
        <div className={Styles.formHintStyles}>Changing the description does not change the category.</div>
      </div>
      <div className={Styles.formRowStyles}>
        <span className={Styles.formLabelStyles}>Date</span>
        <div className={Styles.dateFieldStyles}>
          <div className={cn(Styles.controlStyles, Styles.dateControlStyles)}>
            <button
              type="button"
              className={Styles.dateControlButtonStyles}
              aria-expanded={isCalendarOpen}
              aria-label={`Date, ${formatDayShortWithYear(draft.spentOn)}`}
              onClick={() => setIsCalendarOpen((isOpen) => !isOpen)}
            >
              {formatDayShortWithYear(draft.spentOn)}
              <Calendar size={15} />
            </button>
          </div>
          {isCalendarOpen && (
            <div className={Styles.datePopoverStyles}>
              <DatePicker
                value={draft.spentOn}
                today={todayIso()}
                autoFocus
                onChange={(spentOn) => {
                  onChange({ spentOn });
                  setIsCalendarOpen(false);
                }}
              />
            </div>
          )}
        </div>
      </div>
      <div className={Styles.formActionsRowStyles}>
        <BusyButton variant="primary" isBusy={isSaving} busyLabel="Saving" disabled={!canSave} onClick={onSave}>
          Save changes
        </BusyButton>
        <Button onClick={onCancel}>Cancel</Button>
      </div>
    </>
  );
};

export default ExpenseEditForm;
