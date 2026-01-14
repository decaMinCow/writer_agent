# Proposal: add-novel-to-script-conversion-config

## Why
当前「小说→剧本」(`novel_to_script`) 工作流有两个限制：

1) **来源绑定**：只能从与 run 相同的 `brief_snapshot_id` 读取已提交的小说章节（否则会 `novel_source_missing`）。这会导致“小说已在旧 Snapshot 生成完成，但我想用新规则转写”时无法直接转写。

2) **规则固化**：转写阶段会读取 `brief_snapshot.content.output_spec`（尤其 `script_format/script_format_notes`）。如果想改成短剧强约束格式（如“第一集/1-1/日夜/内外/地点/出场人物/△动作”等），通常需要**新建 Snapshot 并重跑小说**才能把新偏好固化进去。

目标：允许用户**不重跑小说**的情况下，对同一 Brief 下的已生成小说内容应用新的“短剧转写规范”。

## What Changes
- **为 `novel_to_script` Run 增加两个输入：**
  - `source_brief_snapshot_id`：指定小说章节来源 Snapshot（用于选择章节版本 + RAG 证据检索）。
  - `conversion_output_spec`：转写阶段专用的 output_spec 覆盖（例如 `script_format=custom` + `script_format_notes=你的短剧规范全文`）。
- **保持兼容：**未提供上述输入时，默认行为与现在一致（来源=同 Snapshot；格式=Snapshot 的 output_spec）。
- **Web UI 增强：**在“从 Snapshot 创建 Run”里，当选择「小说→剧本」时，额外展示：
  - 小说来源 Snapshot 选择器（默认=当前选中 Snapshot）
  - 转写格式（screenplay/stage/custom）与“转写规范备注”文本框

## Impact / Migration
- 无需 DB migration（配置存入 `workflow_runs.state`）。
- API 兼容（新增字段为 optional）。
- 风险：如果 source Snapshot 不在同一个 Brief 下，先做最小约束：**仅允许同 Brief 内引用**，避免跨作品误用。

