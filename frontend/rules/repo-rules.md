---
doc: repo-rules
scope: frontend
title: Frontend Repository Structure and Patterns
status: current
owner: user
created: 2026-09-09
updated: 2026-09-09
---

# Frontend — Repository Structure and Patterns

The binding ruleset for every file under `frontend/`. It answers one question:
where does this code go, and what shape is it in.

Read it before writing code here. A change that contradicts it says so in the
feature's dev log, per root `CLAUDE.md` rule 5.

## 1. Where these rules came from

Most of what follows is taken from a working system. The `radius` project runs
roughly 160,000 lines of React across six applications on these conventions,
with the same GraphQL client Slashit uses. Its four-file operation folder and
its five component rules are why 160,000 lines still read as though one person
wrote them.

It also shows what rots. §15 lists those failures by name. The largest is a rule
`radius` never wrote down, and §7 writes it down.

## 2. Stack, and what this folder supersedes

The stack is owned by [`process-docs/tech-stack.md`](../../process-docs/tech-stack.md).

| Layer | Choice |
|---|---|
| Framework | React, built with Vite |
| Language | TypeScript |
| GraphQL client | Apollo Client |
| UI state | MobX |
| Typed client | `graphql-codegen`, `typescript-react-apollo` plugin, `near-operation-file` preset |
| Components | shadcn/ui |
| Design system | Produced in Claude Design at stage 2 of each feature |
| Notification transport | GraphQL subscriptions over WebSockets |

**Two supersessions**, both by user direction on 2026-09-09. The tech stack's
own §4 requires a contradiction to be stated rather than left implicit, so both
are stated here.

| Row in tech-stack.md | It says | This folder |
|---|---|---|
| Server state | TanStack Query, over `graphql-request` | Apollo Client |
| Repository | `apps/web`, `apps/api`, `packages/` | `frontend/` and `backend/` at the repository root |

The tech stack rejected Apollo on one argument: a normalised cache is a second
store of what the server holds, and pillar P2 forbids the AI path and the
structured path disagreeing. **That argument is preserved here, not discarded.**
The Apollo cache is not the source of truth. §7 is how.

`process-docs/tech-stack.md` has not been updated to match either supersession
and should be.

## 3. Directory tree

```
frontend/
├── CLAUDE.md
├── rules/
│   └── repo-rules.md            ← this file
├── package.json
├── vite.config.ts
├── codegen.ts
├── schema.graphql               ← exported from the backend. Never hand-edited
├── types.generated.ts           ← codegen output, shared base types. Never edited
├── .env.example
└── src/
    ├── main.tsx
    ├── app/
    │   ├── App.tsx
    │   ├── providers.tsx        ← flat. See §8
    │   └── router.tsx
    ├── api/
    │   ├── lib/                 ← the Apollo layer. See §4
    │   │   ├── apolloClient.ts
    │   │   ├── links.ts
    │   │   ├── cache.ts
    │   │   └── authLink.ts
    │   ├── queries/<Name>/      ← four files each. See §5
    │   ├── mutations/<Name>/
    │   └── subscriptions/<Name>/
    ├── fragments/
    ├── stores/                  ← MobX. The source of truth. See §8
    │   ├── RootStore.ts
    │   └── RecordsStore.ts
    ├── features/<domain>/
    │   ├── controllers/<Name>Controller/
    │   │   ├── <Name>Controller.tsx
    │   │   └── styles.ts
    │   ├── components/
    │   └── utils/
    ├── design-system/           ← §11
    │   ├── tokens.css
    │   ├── components/          ← shadcn primitives, one file each
    │   └── stories/
    ├── components/              ← app-level presentational, cross-feature
    ├── hooks/
    ├── utils/
    ├── constants/
    │   └── apiConstants.ts      ← the APIStatus enum. See §6
    └── types/
```

The design system lives inside `frontend/` rather than a shared package. There
is one web application and no second JavaScript consumer, so a package boundary
would carry cost and buy nothing. The tech stack's Repository row makes the same
argument about Turborepo.

## 4. The Apollo layer

`src/api/lib/` holds the client and nothing else. No component imports from
`@apollo/client` directly except the generated files and the operation hooks.

| File | Holds |
|---|---|
| `apolloClient.ts` | The `ApolloClient` instance. Default `errorPolicy: "all"` |
| `links.ts` | The link chain, and the `graphql-ws` split for subscriptions |
| `cache.ts` | `InMemoryCache`, deliberately without list type policies. §7 |
| `authLink.ts` | Reads the current Supabase session token per request |

**No token refresh queue.** `radius` hand-rolls one, in
`lib/tokenRefreshQueue.ts`, because it issues and refreshes its own JWTs. Slashit
uses Supabase Auth, and the Supabase SDK owns refresh. The auth link asks the SDK
for the current session and attaches the token. Do not port the queue.

**Subscriptions use a split link** over `graphql-ws`, routing subscription
operations to the WebSocket and everything else to HTTP. One client, one auth
path. §9.

## 5. The operation folder

Every GraphQL operation is a folder of four files. This is the strongest
convention in `radius` and it is carried over unchanged.

```
src/api/mutations/CreateRecord/
├── operation.graphql          hand-written document
├── operation.generated.ts     codegen output, colocated
├── responseHandler.ts         the __typename switch. §6
└── useCreateRecord.ts         the public hook. §6
```

This is the same `createRecord` call traced in `backend/.claude/rules/repo-rules.md` §7.
The two documents describe the two ends of one operation, and the union there
matches the switch here member for member.

Rules:

- **The document is hand-written.** Codegen reads it, never writes it.
- **The generated file is colocated**, by the `near-operation-file` preset. It
  is committed, and never edited.
- **Nothing outside this folder imports the generated file.** The hook is the
  public surface.
- **Fragments live in `src/fragments/`** and are shared. A field selection
  repeated in two operations becomes a fragment.

Why a folder and not a file: the error contract, the unwrapping and the hook
change together. Splitting them across three trees means three edits and a
missed one.

## 6. The hook and the response handler

### 6.1 One shape for every operation

```ts
interface UseCreateRecordReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}
```

Every operation hook returns this. Callers learn one shape.

`APIStatus` is a numeric enum in `src/constants/apiConstants.ts`:

```ts
export const API_INITIAL = 0 as const;
export const API_FETCHING = 100 as const;
export const API_SUCCESS = 200 as const;
export const API_FAILED = 400 as const;
export const API_FETCHING_PAGINATION = 600 as const;
```

It is ported from `radius` and it earns its place here specifically because the
client is Apollo. It normalises `networkStatus`, and it makes
pagination-loading a first-class state rather than an `isLoading && hasData`
inference repeated at every call site.

### 6.2 The hook

```ts
const useCreateRecord = (): UseCreateRecordReturnType => {
  const [createRecord, { data, loading, error }] = useMutation<
    CreateRecordMutation,
    CreateRecordMutationVariables
  >(CreateRecordDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs) => {
    const { title, body, kind, onSuccess, onError, onLimitReached } = args;
    createRecord({
      variables: { input: { title, body, kind } },
      onCompleted: (responseData) => {
        handleResponse({
          data: responseData,
          onSuccess,
          onError,
          onLimitReached,
        });
      },
    });
  };

  return {
    triggerAPI,
    apiStatus: getAPIStatusFromMutation(loading, data, error),
    apiError: convertToErrorType(error),
  };
};

export default useCreateRecord;
```

A query hook is the same shape over `useLazyQuery`. It is where `APIStatus`
earns the enum, because `networkStatus` distinguishes a first fetch from a
pagination fetch and a boolean cannot:

```ts
const [getRecords, { data, networkStatus, error }] = useLazyQuery<
  GetRecordsQuery,
  GetRecordsQueryVariables
>(GetRecordsDocument, {
  fetchPolicy: "network-only",
  notifyOnNetworkStatusChange: true,
});

// ...
apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
```

### 6.3 The response handler

The other half of the backend's union contract. `backend/.claude/rules/repo-rules.md` §8
is the first half.

```ts
const useResponseHandler = (): ReturnType => {
  const handleResponse = (args: UseResponseHandlerArgs) => {
    const { data, onSuccess, onError, onLimitReached } = args;
    if (!data?.createRecord) return;

    switch (data.createRecord.__typename) {
      case "Record":
        onSuccess?.(data.createRecord);
        return;
      case "InvalidRecordText":
        onError?.(new Error(data.createRecord.reason));
        return;
      case "RecordLimitReached":
        onLimitReached?.(data.createRecord.limit);
        return;
      default:
        assertNever(data.createRecord);
    }
  };

  return { handleResponse };
};
```

**`assertNever` is required, not optional.**

```ts
const assertNever = (value: never): never => {
  throw new Error(`Unhandled response type: ${JSON.stringify(value)}`);
};
```

A new error type added to a backend union becomes a TypeScript compile error
here. That is the whole point of typed errors, and a `default` that quietly
toasts throws it away.

## 7. The state boundary

The rule `radius` never wrote down. It goes first because everything else
depends on it.

> **MobX stores are the source of truth for server state. The Apollo cache is a
> transport detail.**

Mechanically:

- Operations fetch with `fetchPolicy: "network-only"`.
- `InMemoryCache` is configured without list type policies and without merge
  functions. It is not tuned, because it is not read.
- A response handler's `onSuccess` writes into a store. A controller never
  passes a raw query result down to a component.
- Components read stores. A component that reads `data` from a hook is a defect.

| State | Lives in |
|---|---|
| Records, lists, anything the server sent | A MobX store |
| Filters, selection, search text, sort | A MobX store |
| Whether one modal is open, one input's draft text | Component `useState` |
| A derived value from store fields | A getter on the store, or computed in render |
| A copy of server data kept "for speed" | Nowhere. Delete it |

**Why, and why this is not a reversal.** The tech stack rejected Apollo because
a normalised cache is a second store of the server's data with its own
invalidation rules, and pillar P2 forbids the AI path and the structured path
disagreeing. Running Apollo without leaning on its cache keeps that objection
satisfied. There is exactly one store of server data, and it is the MobX store
that the AI path and the structured path both write into.

The cost is honest and worth naming: more code than letting the cache do it, and
no automatic deduplication of identical concurrent queries beyond
`queryDeduplication`. The benefit is one write path, which §9 turns into the
reason subscriptions are simple here.

## 8. Stores

```ts
class RecordsStoreModel {
  records: Map<string, RecordFragment> = new Map();
  order: string[] = [];
  kindFilter: RecordKind | null = null;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  getAll(): RecordFragment[] {
    return this.order
      .map((id) => this.records.get(id))
      .filter(Boolean) as RecordFragment[];
  }

  setRecords(records: RecordFragment[]): void { /* ... */ }
  upsert(record: RecordFragment): void { /* ... */ }
  remove(id: string): void { /* ... */ }
  clear(): void { /* ... */ }

  static create(): RecordsStoreModel {
    return new RecordsStoreModel();
  }
}
```

Conventions:

- `makeAutoObservable(this, {}, { autoBind: true })` in the constructor.
- A static `create()`. Never `new` at a call site.
- `Map` plus an `order` array for ordered collections. Not a bare array with
  `find`.
- A `clear()` on every store, called on sign out.

**Composed flat, provided once.**

```tsx
export class RootStore {
  records = RecordsStoreModel.create();
  notifications = NotificationsStoreModel.create();
}
```

One `StoreProvider` at the root, one `useStore()` hook. Adding a store is one
line in `RootStore`.

**Not a provider pyramid.** `radius-frontend/apps/points/src/app/providers.tsx`
nests twelve providers, one per store, and adding a store means editing the
pyramid. `providers.tsx` here holds the Apollo provider, the router, the theme
provider, the store provider and the toaster. Five, and it does not grow with
the domain model.

## 9. Subscriptions

A subscription's payload writes into the same store its queries fill.

```
useGetRecords()      → responseHandler → recordsStore.setRecords()
useRecordChanged()   → responseHandler → recordsStore.upsert()
```

This is the payoff of §7. Because the store is the only source of truth, a
subscription needs no cache reconciliation, no `cache.modify`, and no decision
about whether a pushed update should invalidate a query. It calls the same
method the query calls.

The backplane for more than one API instance is open question T-Q3 of the tech
stack and is a backend concern.

## 10. Controllers and components

| | Owns | Never |
|---|---|---|
| Controller | Calling operation hooks, writing to stores, modal and route state | Deep JSX. A controller over ~200 lines is two controllers |
| Component | Rendering props | Calling an operation hook. Reading a store, unless it is an `observer` leaf that genuinely needs one |

A controller lives at
`features/<domain>/controllers/<Name>Controller/<Name>Controller.tsx` with its
`styles.ts` beside it. The suffix is part of the name.

## 11. The design system

Tokens and screens come out of Claude Design at stage 2 of each feature, per the
tech stack. This section governs how they are represented in code.

### 11.1 Two token tiers

```css
@theme {
  /* Tier 1: primitives. Raw values. Named by what they are */
  --color-gray-50: #fafafa;
  --color-gray-900: #171717;
  --color-brand-500: #7033ff;

  /* Tier 2: semantics. Named by what they do. Reference tier 1 */
  --color-background: var(--color-gray-50);
  --color-foreground: var(--color-gray-900);
  --color-primary: var(--color-brand-500);
}
```

**Features use tier 2 only.** `bg-background`, never `bg-gray-50`, never
`bg-[#fafafa]`.

`radius` has only the semantic tier, holding raw hex directly. A rebrand there
means editing roughly fifty values across two files and two modes, by hand, with
no way to check the ramp stayed consistent. Two tiers make it one hue change.

### 11.2 One file, both modes

Light and dark are defined together in `design-system/tokens.css`. Every
semantic token has a value in both. A token defined in only one mode is a
defect.

Tailwind v4 `@theme` is used, which generates the utilities from the tokens
directly. `radius` carries a 200-line Tailwind v3 preset that declares the same
colour map four times, once each for `colors`, `backgroundColor`, `textColor`
and `borderColor`. That file does not need to exist here.

### 11.3 Primitives

- `design-system/components/`, one file per primitive, shadcn CLI managed.
- `cva` for variants. `cn()` for merging.
- A primitive takes no domain type. `Button` knows nothing about a record.
- Primitives are added by the CLI and then owned. Editing one is normal.

### 11.4 Storybook, from the first component

Every primitive has a story. Not eventually.

`radius` has a genuinely good design system and no catalog, and the result is
`NotificationItem`, `PresenceDot` and `ProfileSetupIslandBar` existing in both
its shared layer and its applications, and its chat components built twice. A
component nobody can see is a component somebody rebuilds.

### 11.5 Scroll containers

Every element that scrolls takes the `scroll` class, defined once in
`design-system/tokens.css`. It sets vertical overflow, keeps the scroll inside
the element, and draws the thin scrollbar from the border tokens in both themes.
A feature never writes `overflow-y-auto` or styles a scrollbar itself. Added
2026-10-02 at the user's direction, after the scrollbars drifted from the design.

## 12. Styling

Class strings live in a colocated `styles.ts`, exported as named constants.

```ts
export const containerStyles = "flex h-full min-h-0 w-full flex-col px-4 py-4";
export const toolbarStyles = "flex w-full min-w-0 items-center gap-2";
```

```tsx
import * as Styles from "./styles";

<div className={Styles.containerStyles}>
```

Carried from `radius` unchanged. It keeps JSX readable without a CSS-in-JS
runtime, and it gives every layout decision a name. Conditional classes use
`cn()` at the call site.

## 13. Component conventions

The five rules from `radius-frontend/.cursor/rules/`, ported in substance. They
are the highest-value convention in that repository.

**1. Named arrow components.** Never a `function` declaration, never an inline
component.

**2. `observer` at the default export only.**

```tsx
const RecordCard = (props: RecordCardProps): React.ReactElement => { /* ... */ };
export default observer(RecordCard);
```

Not `const RecordCard = observer(() => ...)`.

**3. Props destructured in the body**, not the parameter list.

```tsx
const RecordCard = (props: RecordCardProps): React.ReactElement => {
  const { record, onSelect } = props;
```

**4. Never a function, store or model in a dependency array.** Not for
`useEffect`, `useCallback` or `useMemo`. Do not satisfy
`react-hooks/exhaustive-deps` by adding them. Stores are stable singletons and
listing them does not track the data you care about; it causes re-runs and, with
network status changes, update loops. Depend on primitives and derived values.

**5. `T | null` on a required property.** Not `field?: T`, not
`field?: T | null`. Absence is checked with `=== null`.

**6. Named `const` booleans, not boolean helper functions.**

```ts
const isTitleWithinLength = trimmedTitle.length <= MAX_TITLE_LENGTH;
const hasTitleChanged = trimmedTitle !== initialTitle;
const shouldSubmitTitle = isTitleWithinLength && hasTitleChanged;
```

Not `isValidTitle()`, not `shouldSubmit()`.

**7. A local string union type takes a `Type` suffix, and its members are
uppercase.**

```ts
type ScreenStateType = "FORM" | "LOADING" | "ERROR" | "SUCCESS";
```

Not `type ScreenState = "form" | "loading"`. The suffix marks it as a locally
defined type at the call site; uppercase members keep a string union visually
distinct from a plain string value being compared or rendered as copy.

## 14. Testing

| Kind | Tool | Covers |
|---|---|---|
| Unit | Vitest | Stores, utilities, response handlers |
| Component | Testing Library | Controllers, with the operation hook mocked |
| Catalog | Storybook | Every design-system primitive, every state |

A response handler test asserts one case per union member, including the
`assertNever` path. This is the frontend half of the backend's rule that every
union member is tested.

## 15. What we deliberately do not do

Each is a real failure in `~/projects/radius`, or a decision the tech stack
already argued.

| Anti-pattern | Why not |
|---|---|
| The Apollo cache as the source of truth | The tech stack's objection to a normalised second store. §7 |
| Type policies and merge functions for lists | Cache tuning nobody reads is cache tuning that will mislead someone |
| A hand-rolled token refresh queue | Supabase's SDK owns refresh. §4 |
| A provider pyramid | Twelve nested providers in `radius`, one per store. §8 |
| Components duplicated between a shared layer and an app | `NotificationItem`, `PresenceDot` and `ProfileSetupIslandBar` exist in both, in `radius`. §11.4 |
| Raw hex or arbitrary Tailwind values in a feature | Defeats the token tier entirely. §11.1 |
| A `default` case that toasts instead of `assertNever` | Turns a compile error into a production surprise. §6.3 |
| A second design system for a future mobile client | `radius` has two, unlinked, because React Native cannot consume its web package. Decide before building, not after |

## 16. Open

| # | Question | Owner |
|---|---|---|
| F-Q1 | `process-docs/tech-stack.md` still names TanStack Query and `apps/web`. Both need updating to match §2, or this folder needs to change | user |
| F-Q2 | How is `schema.graphql` kept in step with the backend: committed and refreshed by a script, or fetched at codegen time from a running API? | user, at epic 000 build plan |
