# Design: Export + formatting (MVP)

## Source selection
- Export uses the latest `artifact_versions` per artifact ordinal for a given `brief_snapshot_id`.
- Novel export: `ArtifactKind.novel_chapter` ordered by `ordinal`.
- Script export: `ArtifactKind.script_scene` ordered by `ordinal`, rendered as Fountain.

## Terminology unification (MVP)
- A snapshot-scoped glossary (key → replacement) can be applied at export time.
- MVP does not rewrite stored artifacts; it affects exported output only (safe + reversible).

