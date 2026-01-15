## Why

当前系统的“剧本相关配置”分散且层级较多：
- `output_spec.script_format` 有多种内置格式（INT/EXT、舞台剧、自定义）
- `output_spec.script_format_notes` 既被用于“直接生成剧本”，也被复用为“小说→剧本”的转写规范
- 小说→剧本还存在 Run 级别的 `conversion_output_spec` 与全局 `novel-to-script-prompt` 的兜底

对单用户产品来说，这会带来较高的学习成本与配置混乱；你希望把系统简化为：
- 只保留两套“全局提示词模板/规范”：**直接生成剧本**一套、**小说→剧本**一套
- 每套全局模板支持**多个预设**，并且在创建 Run 时可以选择使用哪一个
- 不再需要 Brief/Snapshot 级别的转写规范参与优先级

## What Changes

- 新增“提示词模板（Preset）”全局设置：
  - **剧本生成模板**：用于 `script` 工作流（从 Brief 直接生成剧本）
  - **小说→剧本模板**：用于 `novel_to_script` 工作流（从小说章节转写为短剧/剧本）
  - 每类支持：增/删/改预设、设置默认预设
- Run 创建时支持选择要使用的模板（仅保存模板 ID，不复制文本）。
- 工作流执行时根据 Run 选择的模板解析出 `script_format_notes` 并注入到 prompt 上下文：
  - `script`：使用“剧本生成模板”的内容作为 `output_spec.script_format_notes`
  - `novel_to_script`：使用“小说→剧本模板”的内容作为 `output_spec.script_format_notes`
- 简化 UI：不再在全局偏好/Brief 覆盖中暴露多种 `script_format` 选项与“格式备注”混用入口；改为两个清晰入口（剧本生成模板 / 小说→剧本模板）。

## Scope / Non-Goals

- 不追求引入完整 i18n 或复杂的模板版本管理；保持单用户、低复杂度实现。
- 不改小说生成相关的 output_spec（如语言、重试、自动修复次数等）。
- 不要求立刻删除旧接口/旧字段；如需要可提供兼容或迁移策略，但 UI 以新入口为准。

## Impact

- 用户心智显著简化：只需维护两类模板，并在创建 Run 时选择使用哪个。
- 小说→剧本不再被 Snapshot/Brief 的历史备注“污染”，更可控、更容易复现问题。
- 为后续“模板库/一键切换风格”留出清晰扩展点。
