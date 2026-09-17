import { useEffect, useRef } from "react";
import type { ChangeEvent, ClipboardEvent, KeyboardEvent, ReactElement } from "react";

import { cn } from "../../../utils/cn";
import * as Styles from "./styles";

const OTP_LENGTH = 6;
const OTP_INDICES = [0, 1, 2, 3, 4, 5] as const;

interface OtpInputProps {
  value: string;
  onChange: (value: string) => void;
  error?: boolean;
  disabled?: boolean;
  // 02-design.md §7, Focus order: "On entering Verify email or Reset
  // password's code step, focus starts in the first code box."
  autoFocus?: boolean;
}

const OtpInput = (props: OtpInputProps): ReactElement => {
  const { value, onChange, error = false, disabled = false, autoFocus = false } = props;
  const boxRefs = useRef<Array<HTMLInputElement | null>>([]);

  const digits = OTP_INDICES.map((index) => value[index] ?? "");

  const focusBox = (index: number): void => {
    const box = boxRefs.current[index];
    if (box !== null && box !== undefined) box.focus();
  };

  // On mount only: the design says focus starts in the first box on ENTERING
  // the screen. Re-running this when `disabled` flips back after a failed
  // verify would yank focus mid-retype, which is not what it asks for.
  useEffect(() => {
    if (autoFocus) focusBox(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange =
    (index: number) =>
    (event: ChangeEvent<HTMLInputElement>): void => {
      const digit = event.target.value.replace(/[^0-9]/g, "").slice(-1);

      const nextDigits = [...digits];
      nextDigits[index] = digit;
      onChange(nextDigits.join(""));

      const hasEnteredDigit = digit !== "";
      const isNotLastBox = index < OTP_LENGTH - 1;
      if (hasEnteredDigit && isNotLastBox) focusBox(index + 1);
    };

  const handleKeyDown =
    (index: number) =>
    (event: KeyboardEvent<HTMLInputElement>): void => {
      const isBackspaceOnEmptyBox = event.key === "Backspace" && digits[index] === "";
      const isNotFirstBox = index > 0;
      if (isBackspaceOnEmptyBox && isNotFirstBox) {
        const nextDigits = [...digits];
        nextDigits[index - 1] = "";
        onChange(nextDigits.join(""));
        focusBox(index - 1);
      }
    };

  const handlePaste = (event: ClipboardEvent<HTMLInputElement>): void => {
    const pasted = event.clipboardData.getData("text").replace(/[^0-9]/g, "").slice(0, OTP_LENGTH);
    const hasPastedDigits = pasted.length > 0;
    if (!hasPastedDigits) return;

    event.preventDefault();
    onChange(pasted);
    focusBox(Math.min(pasted.length, OTP_LENGTH) - 1);
  };

  return (
    <div className={Styles.otpRowStyles}>
      {OTP_INDICES.map((index) => (
        <input
          key={index}
          ref={(box) => {
            boxRefs.current[index] = box;
          }}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          autoComplete={index === 0 ? "one-time-code" : "off"}
          aria-label={`Digit ${index + 1} of ${OTP_LENGTH}`}
          maxLength={1}
          value={digits[index]}
          disabled={disabled}
          onChange={handleChange(index)}
          onKeyDown={handleKeyDown(index)}
          onPaste={handlePaste}
          className={cn(Styles.otpBoxStyles, error && Styles.otpBoxErrorStyles)}
        />
      ))}
    </div>
  );
};

export default OtpInput;
