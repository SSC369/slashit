/// <reference lib="webworker" />

// injectManifest strategy (see vite.config.ts): this file IS the service
// worker, bundled as-is rather than generated from a serialized config, so
// it can read a POST body to tell GraphQL operations apart. Every GraphQL
// call is a POST to the same URL; only the JSON body's `operationName`
// field distinguishes one from another.

import { cleanupOutdatedCaches, precacheAndRoute } from "workbox-precaching";
import { registerRoute } from "workbox-routing";

import { GRAPHQL_CACHE_NAME } from "./constants/offlineCacheConstants";

declare const self: ServiceWorkerGlobalScope;

precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// registerType: "prompt" (vite.config.ts) means the new worker waits until
// the client explicitly asks it to take over. workbox-window's
// `messageSkipWaiting()` (called from useUpdateAvailable.ts) posts this
// exact message shape.
self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

// FR-40: only these four read operations are cached. Everything else
// (submitCapture, answerPendingCapture, updateTask, ...) always hits the
// network — caching a mutation response would be actively wrong.
const CACHEABLE_OPERATIONS = new Set([
  "GetRecords",
  "GetRecordDetail",
  "GetTasks",
  "GetSettings",
]);

interface GraphQLRequestBody {
  operationName?: string;
  variables?: unknown;
}

/**
 * Builds a cache key that folds in the operation name and variables, not
 * just the URL every GraphQL request shares. Returns null for anything
 * that isn't one of the four cacheable read operations, so the caller
 * knows to skip caching entirely rather than caching under a wrong key.
 */
async function cacheableKeyFor(request: Request): Promise<string | null> {
  let body: GraphQLRequestBody;
  try {
    body = await request.clone().json();
  } catch {
    return null;
  }
  if (!body.operationName || !CACHEABLE_OPERATIONS.has(body.operationName)) {
    return null;
  }
  return `${request.url}?operation=${body.operationName}&variables=${JSON.stringify(
    body.variables ?? {},
  )}`;
}

registerRoute(
  ({ request, url }) => request.method === "POST" && url.pathname === "/graphql",
  async ({ request }) => {
    const cacheKey = await cacheableKeyFor(request);
    if (!cacheKey) {
      // A mutation, or a query this slice doesn't cache. Network only.
      return fetch(request);
    }

    const cache = await caches.open(GRAPHQL_CACHE_NAME);
    try {
      const response = await fetch(request.clone());
      if (response.ok) {
        await cache.put(cacheKey, response.clone());
      }
      return response;
    } catch (networkError) {
      // Prefer fresh data whenever the network is reachable — the app's
      // own MobX stores are already the write-through source of truth
      // (frontend repo-rules.md §7), so a stale SW-level cache should
      // never outrank a real answer. Only offline (FR-40) does the cache
      // get to speak at all.
      const cached = await cache.match(cacheKey);
      if (cached) return cached;
      throw networkError;
    }
  },
  "POST",
);
