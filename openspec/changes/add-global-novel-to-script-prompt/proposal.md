# Proposal: add-global-novel-to-script-prompt

## Why
小说→剧本（`novel_to_script`）在实际使用中经常需要粘贴一整段“转写规范/短剧格式/集场拆分规则”。目前只能在创建 run 时手动填写，重复成本高，也不方便统一调整。

目标：提供一个**全局的“小说→剧本 转写规范”入口**，并确保优先级清晰：
`run 级别备注（原来的转写规范备注）` > `Snapshot/Brief 既有 output_spec 备注` > `全局默认`。

## What Changes
- 新增全局设置：**小说→剧本默认转写规范**（文本）。
- 新增 API：
  - `GET /api/settings/novel-to-script-prompt`
  - `PATCH /api/settings/novel-to-script-prompt`
- `novel_to_script` 执行时：
  - 若 run 提供 `conversion_output_spec.script_format_notes`（即“原来的提示词/备注”已填写），则优先使用它。
  - 若 run 未提供，则优先使用 Snapshot/Brief 既有 `output_spec.script_format_notes`。
  - 若 Snapshot/Brief 也未提供（或为空），才使用全局默认规范作为 `output_spec.script_format_notes` 注入 prompts。
- Web UI：
  - 在“故事资产 / 设置”中新增一个面板，用于编辑全局「小说→剧本默认转写规范」。
  - 在创建 `novel_to_script` run 时，提示“留空则使用 Snapshot/Brief 输出备注；若也为空才使用全局默认”。

## Impact / Migration
- 不需要 DB migration（复用 `app_settings` 表新增一个 key）。
- 行为兼容：未配置全局默认时，`novel_to_script` 生成逻辑与现状一致。
