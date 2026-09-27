import { describe, expect, it } from "vitest";

import { buildMemory } from "../testing/memoryFixture";
import { RootStore } from "./RootStore";

const secret = buildMemory({ id: "m-secret", text: "My test card is 4111 1111 1111 1111" });
const other = buildMemory({ id: "m-other", text: "Preferred airline is Qatar Airways" });

const seedFeed = (store: RootStore): Record<string, string> => {
  const saved = store.capture.addLoadingTurn(`/remember ${secret.text}`);
  store.capture.resolveTurn(saved, { status: "memorySaved", memory: secret, secretCaution: "CARD" });
  const listed = store.capture.addLoadingTurn("/memories");
  store.capture.resolveTurn(listed, { status: "memoryList", memories: [secret, other], searchText: null });
  const kept = store.capture.addLoadingTurn(`/remember ${other.text}`);
  store.capture.resolveTurn(kept, { status: "memorySaved", memory: other, secretCaution: null });
  store.memories.upsert(secret);
  store.memories.upsert(other);
  return { saved, listed, kept };
};

describe("RootStore.forgetMemories, 004 P-3 and P-5", () => {
  it("removes a forgotten memory's save from the open feed and its row from lists", () => {
    const store = new RootStore();
    const { saved, listed, kept } = seedFeed(store);

    store.forgetMemories([secret.id]);

    expect(store.capture.turns.has(saved)).toBe(false);
    const list = store.capture.turns.get(listed);
    expect(list?.status === "memoryList" && list.memories.map((memory) => memory.id)).toEqual([other.id]);
    expect(store.capture.turns.get(kept)?.status).toBe("memorySaved");
    expect(store.memories.get(secret.id)).toBeNull();
    expect(JSON.stringify(store.capture.getAll())).not.toContain("4111");
  });
});
