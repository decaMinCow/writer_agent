以下是当前 workflow run 的信息与用户干预指令。

## Run meta
- kind: {{RUN_KIND}}
- status: {{RUN_STATUS}}

## 当前 run.state（JSON）
{{RUN_STATE_JSON}}

## 目标 step（可选）
{{TARGET_STEP_JSON}}

## 用户干预指令
{{INSTRUCTION}}

请按 system 规则输出 JSON（assistant_message + state_patch）。

