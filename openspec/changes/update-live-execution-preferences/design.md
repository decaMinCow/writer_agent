# Design: Live execution preferences (runtime knobs)

## Goals
- Allow adjusting **fix loop budget** and **autorun retry policy** for runs that already exist.
- Avoid undermining Snapshot-based reproducibility for “creative” constraints.

## Scope
**Live (runtime) keys**
- `output_spec.max_fix_attempts`
- `output_spec.auto_step_retries`
- `output_spec.auto_step_backoff_s`

**Frozen (snapshot) keys**
- Other `output_spec` fields (e.g. `language`, `script_format`, `script_format_notes`) remain sourced from the run’s Snapshot unless a future change introduces explicit per-run overrides.

## Resolution rules
When executing a step (manual or autorun), compute an *effective runtime preferences object*:
1. Read global defaults from `app_settings.output_spec_defaults`.
2. Read per-brief overrides from `briefs.content.output_spec` (keys may be absent).
3. Merge `defaults <- overrides` and extract the three runtime keys.
4. Use these runtime values for:
   - `max_fix_attempts` in fix loops inside `execute_next_step`
   - `auto_step_retries/backoff_s` in autorun retry scheduling

This makes changes to global defaults or per-brief overrides apply to existing runs “from the next step onward”.

## User-visible semantics
- Changes do **not** affect an in-flight LLM call; they take effect on the next step or next retry scheduling decision.
- Snapshot creation continues to store a fully resolved `output_spec` for transparency, but the three runtime knobs may diverge from that frozen snapshot after the user edits preferences.

## Observability
- Optional (nice-to-have): include the resolved runtime knob values in step outputs for debugging.
- UI copy should clarify “these settings affect existing runs starting from the next step”.
