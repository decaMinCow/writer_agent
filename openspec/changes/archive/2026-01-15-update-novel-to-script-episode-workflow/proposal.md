# Proposal: update-novel-to-script-episode-workflow

## Why
当前 `novel_to_script`（小说→剧本）是“按场（scene）逐步生成”的流程，但模型在实际输出时经常会在**单个 scene 的草稿里直接写出整集的多个场景块**（例如同一输出中包含 `1-1/1-2/1-3...`）。当系统继续按 scene 迭代时，就会出现：
- 剧情内容在多个产物之间大量重复（看起来像“写了两遍第一集”）
- 审校/修复卡在格式问题上，难以自动收敛

你的目标（方案 B）是更贴合短剧交付：**1 章小说 = 1 集短剧**，并在集内拆成多个场景，以减少重复并保持连续性。

## What Changes
- 将新创建的 `novel_to_script` run 默认执行为“按章=按集”的 episode 工作流（保留旧的 `nts_scene_*` 流程用于已存在 run 的兼容）：
  - `nts_episode_breakdown`：STEP1 梳理核心关键剧情（事件/冲突/情绪爆点）
  - `nts_episode_draft`：STEP2 生成该集完整短剧剧本（多场景）
  - `nts_episode_critic / nts_episode_fix / nts_episode_commit`：审校-修复-提交闭环
- 强格式要求（custom 短剧格式）：
  - 集头为 `第X集`（仅出现一次）
  - 场号使用 `X.Y`（例如 `11.1`、`11.2`...），同一集内递增且不重复
  - 禁止提示词/执行流程/STEP1/STEP2 原文泄露到产物正文
- 连续性与上下文：
  - 每集生成时带入 `CurrentState` + 之前已提交剧本集的摘要（fact/tone），避免信息断层
  - 提交后更新 `CurrentState`，保证后续集的逻辑连续
- Web UI：
  - `novel_to_script` 的运行进度显示改为“第X集 · 拆解/草稿/审校/修复/提交”
  - 新增/调整与 episode 格式相关的硬错误中文提示

## Export formats（解释）
- `script.txt`：纯文本拼接（不额外加 `== ... ==` 分隔），适合直接阅读/交付。
- `script.fountain`：Fountain 标记文本（会有 `== ... ==` 分隔标题），便于导入编剧工具链（如部分剧本编辑器、后续转换 Final Draft 等）。

## Impact / Migration
- 不需要 DB migration（继续复用 `script_scene` 产物类型承载“每集一份正文”，ordinal 使用章号/集号）。
- 兼容性：
  - 新建 run 默认走 episode 流程（减少重复，更符合短剧交付）。
  - 已存在的 run 若处于旧 `nts_scene_*` 阶段，仍可按旧流程继续（不强制中断）。
