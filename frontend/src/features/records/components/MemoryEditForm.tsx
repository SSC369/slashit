import type { ChangeEvent, ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import Button from "../../../design-system/components/Button";
import { CATEGORY_LABEL, MAX_FACT_LENGTH, MEMORY_CATEGORIES } from "../../../constants/memoryConstants";
import type { MemoryCategory } from "../../../../types.generated";
import { cn } from "../../../utils/cn";
import * as Styles from "./styles";

export interface MemoryDraft {
  text: string;
  category: MemoryCategory | null;
}

/** The form's own error banners: a server refusal the fields cannot show. */
export type MemoryEditBannerType = "NONE" | "FAILED" | "GONE";

interface MemoryEditFormProps {
  draft: MemoryDraft;
  textError: string | null;
  banner: MemoryEditBannerType;
  isSaving: boolean;
  isOffline: boolean;
  onChange: (patch: Partial<MemoryDraft>) => void;
  onSave: () => void;
  onCancel: () => void;
}

const CATEGORY_OPTIONS: { category: MemoryCategory | null; label: string }[] = [
  ...MEMORY_CATEGORIES.map((category) => ({ category, label: CATEGORY_LABEL[category] })),
  { category: null, label: "No category" },
];

/** 004 `MemoryEdit` (FR-18): text with its 500 counter, category, save. */
const MemoryEditForm = (props: MemoryEditFormProps): ReactElement => {
  const { draft, textError, banner, isSaving, isOffline, onChange, onSave, onCancel } = props;
  const trimmedLength = draft.text.trim().length;
  const isOverLimit = trimmedLength > MAX_FACT_LENGTH;
  const isEmpty = trimmedLength === 0;
  const canSave = !isOverLimit && !isEmpty && !isOffline && banner !== "GONE";

  const handleTextChange = (event: ChangeEvent<HTMLTextAreaElement>): void => {
    onChange({ text: event.target.value });
  };

  return (
    <>
      {banner === "FAILED" && (
        <div className={Styles.bannerErrorStyles} role="alert">
          <div>
            <div className={Styles.bannerTitleStyles}>Couldn't save your changes</div>
            <div className={Styles.bannerBodyStyles}>The memory is unchanged. Try again.</div>
          </div>
        </div>
      )}
      {banner === "GONE" && (
        <div className={Styles.bannerWarnStyles} role="alert">
          <div>
            <div className={Styles.bannerTitleStyles}>This memory no longer exists</div>
            <div className={Styles.bannerBodyStyles}>
              It was forgotten from another tab or device, so your edits can't be saved to it.
            </div>
          </div>
        </div>
      )}
      <div className={Styles.formRowStyles}>
        <label htmlFor="memory-text" className={Styles.formLabelStyles}>
          Memory
        </label>
        <textarea
          id="memory-text"
          className={cn(Styles.textareaStyles, (isOverLimit || textError !== null) && Styles.controlErrorStyles)}
          value={draft.text}
          onChange={handleTextChange}
          aria-invalid={isOverLimit || textError !== null}
          aria-describedby="memory-text-counter"
        />
        <div
          id="memory-text-counter"
          className={cn(Styles.counterStyles, isOverLimit && Styles.counterOverStyles)}
        >
          {trimmedLength} / {MAX_FACT_LENGTH}
        </div>
        {isOverLimit && (
          <div className={Styles.fieldErrorStyles}>A memory can be up to {MAX_FACT_LENGTH} characters.</div>
        )}
        {textError !== null && !isOverLimit && <div className={Styles.fieldErrorStyles}>{textError}</div>}
      </div>
      <div className={Styles.formRowStyles}>
        <span className={Styles.formLabelStyles}>Category</span>
        <div className={Styles.segStyles} role="radiogroup" aria-label="Category">
          {CATEGORY_OPTIONS.map((option) => (
            <button
              key={option.label}
              type="button"
              role="radio"
              aria-checked={draft.category === option.category}
              className={cn(Styles.segOptionStyles, draft.category === option.category && Styles.segOptionOnStyles)}
              onClick={() => onChange({ category: option.category })}
            >
              {option.label}
            </button>
          ))}
        </div>
        <div className={Styles.formHintStyles}>
          Changing the text does not change the category. Edits are not checked for conflicts.
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

export default MemoryEditForm;
