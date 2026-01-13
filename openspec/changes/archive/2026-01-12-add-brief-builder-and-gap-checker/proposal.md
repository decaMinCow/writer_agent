# Change: Add Brief Builder and Gap Checker

## Why
The product’s first user-visible capability is turning messy conversational input into a **versioned Creative Brief** that is editable, consistent, and drives downstream generation (novel/script). We need a reliable, structured “intake” loop before implementing long-form generation.

## What Changes
- Add a **Brief Builder** loop:
  - Accept user messages and update the stored Brief draft (structured JSON)
  - Return suggested options for missing fields
  - Support “edit intent” messages like “只改基调/把章数改成 30” as field-targeted updates
- Add a **Gap Checker**:
  - After each message, classify fields into `confirmed`, `pending`, `missing`, `conflict`
  - Produce follow-up questions and a completeness score
- Add minimal persistence for the conversation:
  - Store brief chat messages linked to a brief (for audit and re-runs)
- Add UI wiring:
  - Enable the left “对话” pane to send messages
  - Show updated brief + gap report in the assets pane

## Impact
- Affected specs (new): `brief-builder`, `gap-checker`, `brief-messages`
- Affected code: `apps/api/**` (OpenAI client + prompts + endpoints + migrations), `apps/web/**` (chat pane wiring + views)
- New external dependency: OpenAI API (default provider for MVP)

## Non-Goals (for this change)
- Novel/script generation loops, RAG, KG, critics, change propagation (later changes)
- Multi-user auth/roles (explicitly single-user, no login)

