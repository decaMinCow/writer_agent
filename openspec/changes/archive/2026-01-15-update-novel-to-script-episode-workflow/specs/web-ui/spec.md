# web-ui — Delta (update-novel-to-script-episode-workflow)

## MODIFIED Requirements

### Requirement: UI displays workflow runs with Chinese, phase-aware names
The web UI SHALL display workflow run list items using Chinese labels derived from workflow kind and current cursor phase/index.

#### Scenario: Show novel→script episode progress label
- **GIVEN** a novel→script workflow run has cursor phase `nts_episode_draft` and `chapter_index=3`
- **WHEN** the UI renders the workflow run list
- **THEN** the run SHALL be labeled similar to `小说→剧本 · 第3集 · 草稿`

#### Scenario: Show episode breakdown label
- **GIVEN** a novel→script workflow run has cursor phase `nts_episode_breakdown` and `chapter_index=1`
- **WHEN** the UI renders the workflow run list
- **THEN** the run SHALL be labeled similar to `小说→剧本 · 第1集 · 拆解`
