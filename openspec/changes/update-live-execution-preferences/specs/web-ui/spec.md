# web-ui (delta)

## MODIFIED Requirements

### Requirement: UI supports brief/snapshot creation and preference editing
The web UI SHALL allow the user to create Briefs and Snapshots and to edit preferences without using the raw API.

#### Scenario: Preferences explain live effect on existing runs
- **WHEN** the user views or edits “自动修复最大次数 / 自动跑步骤重试次数 / 重试退避（秒）”
- **THEN** the UI SHALL explain (in short grey helper text) that these settings affect **already-created** workflow runs starting from the next executed step or retry decision
