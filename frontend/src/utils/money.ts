/**
 * Amounts travel as whole paise in a decimal string (006 index §4). They are
 * never turned into a `number`, which loses precision past 2^53; arithmetic
 * goes through BigInt.
 */

const PAISE_PER_RUPEE = 100n;

/** Indian grouping: the last three digits, then pairs. "12000000" -> "1,20,00,000". */
const groupIndian = (digits: string): string => {
  if (digits.length <= 3) return digits;
  const lastThree = digits.slice(-3);
  const rest = digits.slice(0, -3);
  const pairs = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ",");
  return `${pairs},${lastThree}`;
};

/** "12000000" -> "₹1,20,000"; "85050" -> "₹850.50". Paise show only when not zero. */
export const formatRupees = (paise: string): string => {
  const value = BigInt(paise);
  const negative = value < 0n;
  const absolute = negative ? -value : value;
  const rupees = groupIndian((absolute / PAISE_PER_RUPEE).toString());
  const remainder = absolute % PAISE_PER_RUPEE;
  const fraction = remainder === 0n ? "" : `.${remainder.toString().padStart(2, "0")}`;
  return `${negative ? "-" : ""}₹${rupees}${fraction}`;
};

/** Design §7: read aloud as "850 rupees", not "rupee sign 850". */
export const spokenRupees = (paise: string): string =>
  `${formatRupees(paise).replace("₹", "")} rupees`;

/**
 * The edit field's reading of what was typed: "1,200.50", "₹850", "850".
 * Returns paise as a string, or null for anything that is not a positive
 * amount with at most two decimals.
 */
export const parseRupees = (text: string): string | null => {
  const cleaned = text.trim().replace(/^₹\s*/, "").replace(/,/g, "");
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(cleaned);
  if (match === null) return null;
  const [, whole, fraction = ""] = match;
  const paise = BigInt(whole) * PAISE_PER_RUPEE + BigInt(fraction.padEnd(2, "0"));
  return paise > 0n ? paise.toString() : null;
};

/** The edit field's starting text: "85050" -> "850.50", "12000000" -> "120000". */
export const paiseToInput = (paise: string): string => {
  const value = BigInt(paise);
  const remainder = value % PAISE_PER_RUPEE;
  const rupees = (value / PAISE_PER_RUPEE).toString();
  return remainder === 0n ? rupees : `${rupees}.${remainder.toString().padStart(2, "0")}`;
};

/** NFR-6: totals are the exact sum of stored paise. */
export const sumPaise = (amounts: readonly string[]): string =>
  amounts.reduce((total, amount) => total + BigInt(amount), 0n).toString();
