## Why

当前右侧「故事资产」栏混杂了：
- 项目管理（新建/选择 Brief、Snapshots）
- 全局设置（模型提供商、全局偏好、全局转写规范）
- 作品资产（Artifacts、KG/Lint、Open Threads、术语表、导出）

导致信息密度过高、滚动很长、入口不清晰；同时存在多处英文 UI 文案（如 `Workflow Runs`、`Artifacts`、`Versions`、`Fork` 等），对中文用户不友好。

## What Changes

- 右侧栏改为「项目 / 资产 / 设置」三段式结构（Tabs 或 Segmented control），把现有内容按职责分组，减少滚动与认知负担：
  - **项目**：新建/选择 Brief、管理 Snapshots、Brief 偏好覆盖、Gap Report（简报缺口检查）等
  - **资产**：Snapshot 级资产（导出、KG/Lint、Open Threads、术语表、Artifacts + Versions + 编辑器）
  - **设置**：模型提供商（OpenAI 兼容）、全局偏好、小说→剧本全局转写规范
- 将 UI 中用户可见的英文文案替换为清晰中文，并对工作流状态/按钮等提供中文显示（保留内部枚举不变）。
- 为不直观的功能面板提供「灰色说明 + 示例」微文案（可折叠），帮助用户理解用途与操作方式：
  - 伏笔/线索（Open Threads）：什么是线索、如何添加引用、introduced/reinforced/resolved 的含义与示例
  - 一致性检查（KG/Lint）：何时重建/运行、如何从 issue 跳转到产物版本
  - 术语表/导出：术语替换影响范围、导出格式说明、apply glossary 的作用

## Scope / Non-Goals

- 仅调整前端布局与文案，不改后端 API、不引入完整 i18n 框架。
- 不改变现有功能点的逻辑，仅移动入口/替换显示文本。

## Impact

- 用户更容易找到入口（设置不会与资产/项目混在一起）。
- 工作流、资产与设置的概念更清晰；英文术语消除后可读性提升。
