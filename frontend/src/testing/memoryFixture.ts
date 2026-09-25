import type { MemoryFieldsFragment } from "../fragments/MemoryFields.generated";

export const buildMemory = (overrides: Partial<MemoryFieldsFragment> = {}): MemoryFieldsFragment => ({
  id: "memory-1",
  text: "My passport expires in 2030",
  category: "LIFE",
  origin: "command",
  originalInput: "/remember My passport expires in 2030",
  createdAt: "2026-09-25T09:41:00+00:00",
  updatedAt: "2026-09-25T09:41:00+00:00",
  ...overrides,
});
