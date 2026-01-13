# Design: Global defaults + per-brief overrides (preferences)

## Goals
- Provide a **global default** `output_spec` editable in UI.
- Allow each Brief to **override** any subset of `output_spec`.
- Ensure workflows stay reproducible by having each Brief Snapshot contain the **effective** `output_spec`.

## Data Model
- Add `app_settings` table:
  - `key` (unique string; e.g. `output_spec_defaults`)
  - `value` (JSON)
  - timestamps
- Store global defaults under `output_spec_defaults` (e.g. `{ language, script_format, script_format_notes }`).

## Semantics
- **Global defaults** provide baseline values.
- **Brief overrides** are optional fields stored under `brief.content.output_spec`.
  - Missing keys mean “inherit from global defaults”.
  - Clearing an override removes the key from `brief.content.output_spec`.
- **Brief Snapshot** stores resolved `content.output_spec = merge(global_defaults, brief_overrides)` at snapshot creation time.
  - This keeps generation runs stable even if global defaults change later.

## API
- `GET /api/settings/output-spec` → returns global defaults (with server-side defaults if unset).
- `PATCH /api/settings/output-spec` → updates global defaults.
- `PATCH /api/briefs/{id}/output-spec`:
  - Accepts optional fields and supports clearing overrides by allowing explicit `null` (distinguish “unset” vs “not provided” via `model_fields_set`).

## UI
- Add “Global Preferences” section (right panel):
  - Script format dropdown + notes
  - Save applies to global defaults.
- Add “Brief Overrides” section (only when a Brief is selected):
  - Show effective values (global + override).
  - Provide “Use global” toggles (clears per-brief override fields).
- Add “Create Brief” + “Create Snapshot” controls (inline forms; no auth).

## Backwards Compatibility
- Existing Briefs may already have `output_spec` populated with previous per-brief defaults.
  - They will behave as overrides until cleared.
  - UI will provide a “Reset to global” action (clears fields) so global defaults can take effect.

