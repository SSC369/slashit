import { afterEach, describe, expect, it, vi } from "vitest";

import { GRAPHQL_CACHE_NAME } from "../../constants/offlineCacheConstants";
import { clearOfflineReadCache } from "./offlineReadCache";

describe("clearOfflineReadCache", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("deletes the service worker's GraphQL read cache (002 FR-24, 004 NFR-2)", async () => {
    const deleteCache = vi.fn().mockResolvedValue(true);
    vi.stubGlobal("caches", { delete: deleteCache });

    await clearOfflineReadCache();

    expect(deleteCache).toHaveBeenCalledWith(GRAPHQL_CACHE_NAME);
  });
});
