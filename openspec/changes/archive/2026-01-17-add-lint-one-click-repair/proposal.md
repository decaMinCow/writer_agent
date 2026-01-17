# Change: 一致性问题一键修复（Lint Repair）

## Why
一致性检查（KG / Lint）能够发现问题，但用户需要逐条跳转并手动重写，成本高、易遗漏。需要提供“一键修复”能力：对可定位到具体产物版本的问题，自动创建修复后的新版本，并便于再次运行检查验证修复效果。

## What Changes
- 后端新增一致性问题“一键修复”接口：对当前 Snapshot 下可修复的问题（带 `artifact_version_id`）批量创建修复版本。
- 修复策略（MVP）：
  - 对同一 `artifact_version_id` 的多条问题合并为一次修复指令。
  - 使用 AI 重写该产物全文（创建新版本，不覆盖旧版本），尽量只改与问题相关的部分。
  - 对无法定位到具体版本的问题（如重复 ordinal）跳过并返回统计。
- 前端在“一致性检查（KG / Lint）”面板增加「一键修复」按钮与结果提示，并在修复后引导用户重新运行检查。

## Non-Goals
- 不尝试对所有问题都 100% 自动修复（例如：需要人工决策的结构性问题）。
- 不直接删除/覆盖原产物版本（保持可回滚）。

## Impact
- Affected specs (delta): `story-linter`, `web-ui`
- Affected code:
  - API: `apps/api/app/api/routers/analysis.py`
  - UI: `apps/web/src/routes/+page.svelte`
  - Tests: `apps/api/tests/*`

