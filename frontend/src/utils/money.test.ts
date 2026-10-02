import { describe, expect, it } from "vitest";

import { formatRupees, paiseToInput, parseRupees, spokenRupees, sumPaise } from "./money";

describe("formatRupees", () => {
  it("groups in the Indian way (F-3)", () => {
    expect(formatRupees("12000000")).toBe("₹1,20,000");
    expect(formatRupees("85000")).toBe("₹850");
    expect(formatRupees("420000")).toBe("₹4,200");
    expect(formatRupees("100")).toBe("₹1");
  });

  it("formats a 10-digit rupee amount without loss (F-3)", () => {
    expect(formatRupees("123456789012")).toBe("₹1,23,45,67,890.12");
    expect(formatRupees("999999999999999999")).toBe("₹9,99,99,99,99,99,99,999.99");
  });

  it("shows paise only when they are not zero", () => {
    expect(formatRupees("85050")).toBe("₹850.50");
    expect(formatRupees("85005")).toBe("₹850.05");
  });
});

describe("spokenRupees", () => {
  it("reads as rupees, not the sign", () => {
    expect(spokenRupees("85000")).toBe("850 rupees");
  });
});

describe("parseRupees", () => {
  it("reads what the edit field accepts", () => {
    expect(parseRupees("850")).toBe("85000");
    expect(parseRupees("₹1,200.50")).toBe("120050");
    expect(parseRupees(" 1,20,000 ")).toBe("12000000");
    expect(parseRupees("850.5")).toBe("85050");
  });

  it("rejects zero, negatives, three decimals and words", () => {
    expect(parseRupees("0")).toBeNull();
    expect(parseRupees("0.00")).toBeNull();
    expect(parseRupees("-5")).toBeNull();
    expect(parseRupees("850.505")).toBeNull();
    expect(parseRupees("abc")).toBeNull();
    expect(parseRupees("")).toBeNull();
  });
});

describe("paiseToInput", () => {
  it("round-trips through parseRupees", () => {
    expect(paiseToInput("85050")).toBe("850.50");
    expect(paiseToInput("12000000")).toBe("120000");
    expect(parseRupees(paiseToInput("123456789012"))).toBe("123456789012");
  });
});

describe("sumPaise", () => {
  it("adds past 2^53 exactly", () => {
    expect(sumPaise(["9007199254740993", "1"])).toBe("9007199254740994");
    expect(sumPaise([])).toBe("0");
  });
});
