# Change: Add export + formatting tools (Markdown + Fountain MVP)

## Why
Users need deliverables. The IDE must export novels and scripts in standard formats and provide basic formatting utilities (terminology unification).

## What Changes
- Backend:
  - Export compiled novel text (latest chapter versions per snapshot) as Markdown/text.
  - Export compiled script scenes (latest scene versions per snapshot) as Fountain (MVP).
  - Basic terminology replacement tool with preview and “export with replacements”.
- Frontend:
  - Export buttons per snapshot (download).
  - Simple terminology settings UI (MVP).

## Impact
- Affected specs (new): `exports`
- Affected specs (update): `web-ui`

## Non-Goals (for this change)
- Final Draft FDX output (can be added later)
- Full-book LLM polish pipeline (can be added as a separate change)

