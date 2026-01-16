# Change: 移除 Brief 输出偏好覆盖（统一使用全局默认）

## Why
当前“输出偏好（本 Brief 覆盖）”让理解成本偏高，用户希望简化为仅使用全局默认，界面更清晰、更容易理解与维护。

## What Changes
- UI 移除“输出偏好（本 Brief 覆盖）”编辑区域与相关交互。
- 生成 Snapshot 时仅使用全局默认输出偏好，不再合并 Brief 覆盖字段。
- API 保留全局偏好设置入口，Brief 级覆盖不再参与生效。

## Impact
- Affected specs (delta): `web-ui`, `brief-snapshots`, `global-settings`
- Affected code: `apps/web/src/routes/+page.svelte`, `apps/api` (snapshot creation logic)
