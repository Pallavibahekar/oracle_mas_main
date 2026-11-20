# Frontend interview notes — Oracle MAS Console

Short version of what to say if an interviewer asks about this work.

## "What did you build?"

"I added a React + TypeScript console to a Python multi-agent project that previously had no UI. The backend requires Bedrock credentials, Qdrant and Neo4j, so I built the frontend against a typed mock event stream that has the same contract as the future SSE endpoint. That let me demonstrate routing, streaming agent activity, source citations and run history with a single `npm run dev`."

## "What was the hardest part?"

"Keeping the mock replaceable. I made the transport an async generator that yields a small union of events — `start`, `step`, `complete`, `error` — and threaded an `AbortSignal` through it. The React layer only knows that contract. Replacing the simulation with a real `fetch` stream is a one-file change."

## "How does state work?"

"One `RunsProvider` holds `runs`, `activeRun`, `error` and `isRunning`, exposed through a `useRuns` hook. Dashboard metrics are derived from `runs` instead of being stored separately, so they cannot drift. While consuming the stream I keep a local accumulator and publish each snapshot; I deliberately avoid calling `setRuns` from inside a `setActiveRun` updater, because StrictMode can double-invoke updaters and duplicate the run."

## "How did you test it?"

"Unit tests for the pure routing function and event ordering, a component test for status rendering, and an integration test that types a query into the playground and waits for the streamed answer. `streamDelayMs` is injectable on the provider so tests run instantly. CI runs lint, tests and a production build on Node 22."

## "What would you do next?"

1. Add an SSE endpoint in FastAPI that emits the same event names and replace `streamRun`.
2. Persist run history in the backend instead of local memory.
3. Add optimistic cancellation UI wired to the existing `AbortSignal`.
4. Move routing explanation from static copy to live data returned by the router agent.

## Honest limitations

- Data is seeded/mocked; nothing calls AWS, Qdrant or Neo4j from the browser.
- Run history is in memory and resets on refresh.
- The keyword routing rule is intentionally simple; the real router uses LangGraph and an LLM.
- No authentication or multi-user support.

Saying these out loud is a strength: it shows you know what is real, what is simulated, and where the seams are.
