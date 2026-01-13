# Change: Stream brief chat responses (SSE)

## Why
Brief building currently uses a single request/response. When the model takes time, the UI appears stalled and the user cannot tell if the system is still working.

## What Changes
- Add a streaming endpoint for brief messages that emits **SSE** events while the assistant response is being generated.
- Update the web UI to render assistant output incrementally (real-time typing) and then finalize by applying the brief patch + storing messages.
- Keep the existing non-stream endpoint as a fallback for compatibility and tests.

## Impact
- Affected specs: `brief-messages` (modified), `web-ui` (modified)
- Affected backend: brief message router + OpenAI chat client streaming support.
- Affected frontend: chat send flow uses streaming fetch + SSE parser.

