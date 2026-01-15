## 1. Implementation

- [x] Add global setting storage in `app_settings` for novel→script prompt defaults.
- [x] Add settings API routes:
  - [x] `GET /api/settings/novel-to-script-prompt`
  - [x] `PATCH /api/settings/novel-to-script-prompt`
- [x] Apply prompt precedence in `novel_to_script` execution:
  - [x] Run-level `conversion_output_spec.script_format_notes` overrides everything
  - [x] Else fall back to existing snapshot output spec notes
  - [x] Else use global novel→script default prompt
- [x] Update NTS planner prompt to treat `output_spec.script_format_notes` as high-priority conversion rules when present.
- [x] Add Web UI panel to edit the global novel→script prompt.
- [x] Update novel→script run creation UI to indicate blank notes uses snapshot/brief notes, then global.

## 2. Validation

- [x] Add backend test for the new settings endpoints.
- [x] Add backend test ensuring `novel_to_script` uses global prompt when run notes are not provided.
- [x] Run `cd apps/api && uv run pytest`.
- [x] Run `cd apps/web && npm run check`.
- [x] Run `openspec validate add-global-novel-to-script-prompt --strict`.
