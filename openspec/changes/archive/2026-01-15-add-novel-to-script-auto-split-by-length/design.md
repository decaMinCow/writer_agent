## Overview

为 `novel_to_script` 增加一种“按目标字数自动拆集”的可选策略：

- 每章先做一次 STEP1（章级拆解 + 拆集方案），得到该章要拆成的“剧本集单元列表”。
- 再按单元逐集生成/审校/修复/提交，直到该章完成，然后进入下一章。

本设计保持现有默认（1章=1集）不变；新策略通过 run 配置启用，避免破坏既有行为。

## Key Decisions

### 1) 字数范围来源（“按提示词”）

选择的“小说→剧本模板（prompt preset）”文本会被注入 `output_spec.script_format_notes`。

系统在运行时将从该文本中 **尝试解析一个字数区间**（例如 `500-800字`、`500–800 字`、`500~800字`、`500到800字`）：
- 解析成功：作为该 run 的 `target_chars_min/target_chars_max`
- 解析失败：回退到默认 `500–800`

这样用户改模板即可改变拆分目标，无需额外新增复杂配置面板。

### 2) 字数统计口径

按你确认的规则：**去掉空格与标点**后的字符数。

实现要点（Python）：
- 去掉所有空白（`str.isspace()`）
- 去掉 Unicode 标点（`unicodedata.category(ch).startswith("P")`）
- 剩余字符数作为 `content_char_count`

### 3) “允许小幅超出”策略

为了避免过度修复导致卡死：
- 定义 `soft_max = max_chars * (1 + overflow_ratio)`，默认 `overflow_ratio=0.10`（10%）
- `content_char_count > soft_max`：视为硬错误，触发修复
- `max_chars < content_char_count <= soft_max`：允许提交，但在审校结果中记录为软提醒（不阻断）

### 4) 工作流状态与编号

动态拆分会导致“剧本集编号”不再等于 `chapter_index`。因此：
- 引入 `state.script_episode_index_next`（全局递增的剧本集序号，从 1 开始）
- 每章拆分出的第 k 集，使用 `episode_index = script_episode_index_next + (k-1)`
- 提交时：
  - `ArtifactKind.script_scene` 的 `ordinal` 使用 `episode_index`
  - `ArtifactVersion.meta` 写入 `source_chapter_index` 与 `chapter_episode_sub_index`

### 5) 新增章级拆分计划（STEP1）

新增 LLM 输出 JSON schema（示意）：

```json
{
  "chapter_index": 1,
  "chapter_title": "…",
  "core_plot": ["…"],
  "episodes": [
    {
      "sub_index": 1,
      "title": "（可空）",
      "key_events": ["…"],
      "conflicts": ["…"],
      "emotional_beats": ["…"],
      "hook_idea": "…"
    }
  ]
}
```

这一步只做一次；后续每集 draft 只消耗对应 `episodes[sub_index]` 的信息，避免重复。

## Workflow Phases (new mode)

在 `novel_to_script` run 中，当启用 `split_mode=auto_by_length`：
- `nts_chapter_plan`：生成章级拆分计划（STEP1）
- `nts_episode_draft`：按某个 sub-episode 生成一集剧本（STEP2）
- `nts_episode_critic`：格式 + 字数 + 其它硬约束审校
- `nts_episode_fix`：定向修复
- `nts_episode_commit`：提交产物并推进到下一 sub-episode / 下一章

旧模式（1章=1集）继续沿用现有 phases，保持兼容。

## UI Changes

创建 `小说→剧本` run 时新增一个简单开关：
- `按章（1章=1集）`
- `按字数自动拆集（动态）`

启用后，run 会在 state 写入 `split_mode=auto_by_length`；其余配置不变（仍可选择来源 snapshot 与模板）。
