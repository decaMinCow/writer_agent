# Design: add-autorun-step-auto-retries

## Goals
- Autorun 在遇到**可恢复**错误时自动重试，减少人工干预。
- 重试可配置（全局默认 + per-brief override），并带退避，避免打爆提供商。
- 不吞错误：每次失败仍会记录 `workflow_step_runs`，便于回溯。

## Non-goals
- 不保证 100% “永不失败”：例如持续性鉴权错误、长期 provider 不可用、硬一致性检查失败等仍会终止。
- 不引入复杂的作业队列/分布式重试（保持 MVP 简洁）。

## Retryable errors
仅对“很大概率下一次会成功”的失败自动重试：
- 网络/连接/超时类：`APIConnectionError`、`APITimeoutError`、SSL EOF、`ConnectError`、`RemoteProtocolError` 等。
- 速率/服务端类：`APIStatusError` 且 status code ∈ {408, 409, 429, 500, 502, 503, 504}。
- 输出格式/解析类：`JSONDecodeError`、`ValidationError`、`expected_json_object` 等（LLM 偶发输出不严格、截断）。

明确不自动重试：
- `hard_check_failed`、`max_fix_attempts_exceeded` 等业务硬失败（需要改约束或调高 max_fix_attempts）。
- 4xx（401/403/404/405 等）通常为配置/能力不支持（已对 embeddings 405 做降级，不再让 run 失败）。

## State tracking
在 `workflow_runs.state` 增加内部字段（不作为 API schema 强约束）：
- `_autorun_retry.step_name`：最近一次失败的 step_name
- `_autorun_retry.attempt`：同一 step_name 的连续失败次数（成功后清空）

## Backoff
指数退避（封顶）：
- `delay = min(auto_step_backoff_s * 2^(attempt-1), 30s)`，可加少量 jitter。
在等待期间如果用户点击停止 autorun，应尽快退出（用 `stop_event.wait()` + timeout 实现）。

