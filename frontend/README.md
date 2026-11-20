# Oracle MAS Console

A standalone React + TypeScript frontend for the Oracle MAS multi-agent system. It runs **without the Python backend, AWS credentials, Qdrant or Neo4j** by using a typed mock event stream with the same interface as the real SSE endpoint.

## Why it exists

The backend in this repository needs Bedrock credentials and local vector/graph databases, so it cannot be demoed on a fresh machine. This console makes the product demoable and gives a clean seam for swapping in the real API later.

## Run it

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

Other scripts:

```bash
npm test         # Vitest + React Testing Library
npm run lint     # ESLint, zero warnings allowed
npm run build    # typecheck + production bundle
npm run preview  # serve the production build
```

## What you can do

- **Dashboard** — derived metrics, agent fleet, recent runs.
- **Playground** — submit a request, watch the router delegate to specialists, and read the synthesized answer with sources.
- **Agents** — capabilities and the routing rules used by the demo.
- **Run history** — filter by status and expand any run to inspect its timeline.
- **Integrations** — what each real backend dependency does and why it is mocked here.

## Architecture

```
src/
├── components/     Presentational + layout components
├── data/           Static agent metadata
├── pages/          Route-level screens
├── services/
│   └── mockApi.ts  Pure routing rule + async generator that streams RunEvents
├── state/
│   └── runs.tsx    RunsProvider + useRuns hook (single source of truth)
├── types.ts        Shared domain types
└── test/setup.ts   Testing Library matchers
```

### The API seam

`streamRun(query, { delayMs, signal })` is an **async generator** yielding `start`, `step`, `complete` and `error` events. The UI only consumes that event contract; it does not know whether events come from a local simulation or a real network stream.

To connect the Python backend, replace the body of `streamRun` with a `fetch` to an SSE endpoint that emits the same JSON events. No component or state changes are required. `AbortSignal` is already threaded through so the UI can cancel in-flight work.

### Design decisions

- **Mock, but honest**: the sidebar and integrations page clearly label demo mode. Nothing pretends to have called AWS.
- **Pure routing logic**: `chooseRoute` is a separate exported function so it can be unit tested without rendering React.
- **Derived state, no duplicated state**: dashboard metrics are computed from `runs`; only runs, active run, error and loading flag are stored.
- **No state update inside a state updater**: the stream accumulator is a local variable, so React StrictMode double-invocation cannot duplicate a run.
- **Accessible basics**: labelled inputs, `aria-expanded` on history rows, `aria-live` on the current run, visible focus rings.

## Tests

- `mockApi.test.ts` — routing decisions, event ordering, empty-query error path.
- `StatusBadge.test.tsx` — status presentation.
- `PlaygroundPage.test.tsx` — full user flow from typing a query to rendered answer.

CI (`.github/workflows/frontend-ci.yml`) runs lint, tests and build on every change under `frontend/`.
