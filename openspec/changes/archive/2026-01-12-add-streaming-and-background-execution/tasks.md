## 1. Implementation
- [x] 1.1 Add in-process workflow event hub (publish/subscribe) and SSE endpoint
- [x] 1.2 Add autorun start/stop endpoints (server-driven loop over next-step execution)
- [x] 1.3 Publish events from workflow execution (run/step lifecycle)
- [x] 1.4 Add web SSE client + render live run progress; keep manual next-step
- [x] 1.5 Add tests: autorun stop behavior + SSE basic event contract

## 2. Validation
- [x] 2.1 `openspec validate add-streaming-and-background-execution --strict`
- [x] 2.2 Backend: `uv run ruff check .` and `uv run pytest`
- [x] 2.3 Frontend: `npm run lint` and `npm run check`
