## 1. Specification

- [x] Add `web-ui` spec deltas for:
  - [x] Right pane layout: Project/Assets/Settings grouping.
  - [x] Chinese UI labels for common workflow and asset terms.

## 2. Implementation (Web)

- [x] Add a right-pane tab state (persist last selection locally).
- [x] Re-group existing right-pane panels into:
  - [x] 项目：Brief/Snapshot 管理 + Gap Report + Brief 偏好覆盖
  - [x] 资产：导出 + KG/Lint + Open Threads + 术语表 + Artifacts/Versions/编辑
  - [x] 设置：模型提供商 + 全局偏好 + 全局转写规范
- [x] Add contextual help microcopy (grey helper text, optionally collapsible):
  - [x] Open Threads（伏笔/线索）：用途、步骤示例、引用类型解释（introduced/reinforced/resolved）
  - [x] KG/Lint：何时运行、如何跳转到问题版本、LLM 开关含义
  - [x] 术语表/导出：术语替换范围、导出格式说明、导出时应用术语表的效果
- [x] Replace/translate remaining user-facing English strings:
  - [x] Panel titles (e.g., `Workflow Runs`, `Artifacts`, `Versions`, `Gap Report`)
  - [x] Buttons (e.g., `Fork`, `Forking…`)
  - [x] Status labels (`queued/running/paused/succeeded/failed/canceled`)
  - [x] Field labels (`Base URL`, `Chat Model`, `Embeddings Model`, `Timeout`, `Max Retries`, `default`)
  - [x] Digest labels (`Fact Digest`, `Tone Digest`, `error`)
  - [x] Open Threads terms (`introduced/reinforced/resolved`, thread status `open/closed`)

## 3. Validation

- [x] Run `cd apps/web && npm run check`.
- [x] Sanity check: all existing actions still reachable from right pane (settings/edit/export/assets).
- [x] Run `openspec validate update-ui-right-pane-layout-zh --strict`.
