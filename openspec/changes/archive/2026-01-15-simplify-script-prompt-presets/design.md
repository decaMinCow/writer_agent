## Overview

本变更将“剧本相关配置”从“多种格式枚举 + 多层备注优先级”收敛为：

- **两类模板（Preset Catalog）**：
  1) `script`（直接生成剧本）模板
  2) `novel_to_script`（小说→剧本）模板
- 每类模板支持**多个预设**（可命名），并可设置“默认预设”。
- Run 创建时只保存 `prompt_preset_id`（字符串），执行时解析到预设文本并注入到 `output_spec.script_format_notes`。

## Data Model

全局设置新增一个 setting key（单用户 JSON 存储）：

```json
{
  "script": {
    "default_preset_id": "default",
    "presets": [
      { "id": "default", "name": "默认", "text": "" }
    ]
  },
  "novel_to_script": {
    "default_preset_id": "short_drama",
    "presets": [
      { "id": "short_drama", "name": "短剧默认", "text": "" }
    ]
  }
}
```

约束与容错：
- `id`：字符串（可用 UUID），仅需在同一类中唯一。
- 若 `default_preset_id` 不存在或为空：回退到 presets[0]；若 presets 为空则视为无模板（`text=None`）。
- 允许 `text` 为空字符串（表示不额外约束，仅用内置 system prompt）。

## Run Configuration

WorkflowRun 创建 payload 增加可选字段：
- `prompt_preset_id?: string | null`

解释：
- `kind=script`：`prompt_preset_id` 在“script 模板库”中查找；为空则用其默认预设。
- `kind=novel_to_script`：`prompt_preset_id` 在“novel_to_script 模板库”中查找；为空则用其默认预设。
- 其它 kind（novel）忽略该字段（并在 API 层拒绝不支持输入）。

Run state 存储：
- `state["prompt_preset_id"] = "<id>"`（仅保存 id，便于复现与调试）

## Prompt Injection Strategy

目标是让现有 prompt 文件尽量不改：
- 现有 prompt 已通过 `output_spec.script_format_notes` 承载“强约束/转写规范”。
- 因此在执行时构造 `output_spec` 时，将选中的 preset `text` 写入 `output_spec.script_format_notes`。

对小说→剧本：
- 取消 Brief/Snapshot 的 `output_spec.script_format_notes` 参与转写规范优先级（避免历史备注污染）。
- 仅使用“小说→剧本模板（preset）”注入 `script_format_notes`。

对直接生成剧本：
- 使用“剧本生成模板（preset）”注入 `script_format_notes`。

## UI Changes

右侧「设置」新增两个面板：
- 剧本生成模板：管理 presets + 选择默认
- 小说→剧本模板：管理 presets + 选择默认

工作流创建处：
- 当选择 `script` 或 `novel_to_script` 时，展示“选择模板”的下拉框（默认选中各自的默认预设）。

同时简化“输出偏好”：
- 不再对用户暴露 `script_format` 多选项与通用“格式备注”入口（避免与模板入口重复、混淆）。
- 仍保留语言、自动修复次数、自动重试等稳定选项。

## Backward Compatibility

- 保留旧数据字段（如 Snapshot 中已有的 `output_spec.script_format_notes`），但小说→剧本流程不再读取它作为转写规范。
- 可保留旧 API 字段以兼容（若存在），但 Web UI 不再使用旧入口。
