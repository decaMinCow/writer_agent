# Design: add-novel-to-script-conversion-config

## Overview
为 `novel_to_script` 工作流提供“来源 Snapshot + 转写专用 output_spec”两类输入，让用户在不重跑小说的情况下切换短剧转写规范。

## Data Model
不新增表结构，配置写入 `workflow_runs.state`（便于回放与审计）：

- `state.novel_source_snapshot_id`: string(UUID)
  - 仅对 `novel_to_script` 生效
  - 默认值：`run.brief_snapshot_id`
- `state.conversion_output_spec`: object
  - 形状对齐 `OutputSpecOverrides`（允许部分字段）
  - 用于覆盖 `brief_snapshot.content.output_spec`，只影响转写流程（Scene List + Scene Draft/critic/fix/commit）

## Execution Semantics
### Source selection
- 读取 brief（约束/人物/世界观）仍以 `run.brief_snapshot_id` 的 Snapshot 为准（run 的“配置/归属”）。
- 小说章节来源与证据检索使用 `source_snapshot_id`：
  - `select latest novel chapter versions` 使用 `source_snapshot_id`
  - `retrieve_evidence` 使用 `source_snapshot_id`（因为 memory_chunks/embeddings 绑定到来源 Snapshot）
- 生成的剧本产物（artifact versions）仍写入 `run.brief_snapshot_id`，确保 UI 层级（Brief→Snapshot→Runs→Artifacts）一致。

### Conversion output spec
- 计算 `effective_output_spec = deep_merge(snapshot.output_spec, conversion_output_spec)`
- 在 prompts 中：
  - 作为 `BRIEF_JSON.output_spec` 提供给 `nts_scene_list`
  - 作为 `SCENE_JSON.output_spec` 提供给 `nts_scene_draft`（现有系统 prompt 已支持 `custom` + `script_format_notes`）

## API + UI
- API：`POST /api/workflow-runs` 扩展 optional 字段：
  - `source_brief_snapshot_id?: UUID`
  - `conversion_output_spec?: OutputSpecOverrides`
- UI：在创建 Run 的面板里，当 `kind=novel_to_script` 时显示输入项并传入 API。

## Validation / Guardrails
- `source_brief_snapshot_id` 必须存在且属于同一个 `brief_id`（与 run 的 snapshot 同 Brief），否则 400。
- `conversion_output_spec` 仅用于 merge，不覆盖/写回 brief。

