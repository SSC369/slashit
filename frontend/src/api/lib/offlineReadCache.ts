import { GRAPHQL_CACHE_NAME } from "../../constants/offlineCacheConstants";

/**
 * Empties the offline copy of GraphQL reads. It is keyed by operation, not by
 * user, so it must not outlive a session (002 FR-24), and it can hold a memory
 * the user has since forgotten (004 NFR-2). The next online read refills it.
 */
export const clearOfflineReadCache = async (): Promise<void> => {
  if (!("caches" in window)) return;
  await caches.delete(GRAPHQL_CACHE_NAME);
};
