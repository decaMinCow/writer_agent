# Change: add-autorun-step-auto-retries

## Why
长文本生成在“OpenAI 兼容但不稳定”的提供商上经常出现可恢复的失败（SSL 断连、偶发 5xx/429、输出格式不严格导致解析/校验失败）。当前服务端 autorun 在任一步失败后会停止，导致用户必须人工点击“重试/重试自动”，无法做到真正的全自动跑完。

## What Changes
- 在**服务端 autorun** 中加入“可恢复失败”的**自动重试策略**（带退避 backoff），避免一次偶发失败就中断整条 run。
- 增加可配置项（全局默认 + 每个 Brief 可覆盖）：
  - `output_spec.auto_step_retries`：autorun 下单个 step 的最大自动重试次数。
  - `output_spec.auto_step_backoff_s`：autorun 下自动重试的基础退避秒数（指数退避、封顶）。
- 将“哪些错误会自动重试”做成明确的判定规则（网络/连接/超时、可恢复的 APIStatus、JSON/Schema 解析校验类错误）。
- 通过现有 SSE `log` 事件推送重试信息，便于 UI 观察（不要求新增 UI 日志面板）。

## Impact
- Affected specs:
  - `execute-workflows`（autorun 行为）
  - `global-settings`（默认 output_spec 字段扩展）
  - `web-ui`（设置面板增加两个字段）
- Affected code (expected):
  - `apps/api/app/api/routers/workflows.py`（autorun loop 重试）
  - `apps/api/app/services/settings_store.py` / `apps/api/app/schemas/settings.py`（output_spec defaults）
  - `apps/api/app/schemas/briefs.py` / `apps/api/app/api/routers/briefs.py`（Brief override）
  - `apps/web/src/routes/+page.svelte` / `apps/web/src/lib/api.ts`（UI + types）

