from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.llm.client import LLMClient
from app.schemas.workflow_interventions import WorkflowInterventionResult
from app.services.prompting import extract_json_object, load_prompt, render_prompt


async def parse_workflow_intervention_output(
    *,
    llm: LLMClient,
    raw_output: str,
    max_attempts: int = 2,
) -> WorkflowInterventionResult:
    try:
        payload = extract_json_object(raw_output)
        return WorkflowInterventionResult.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        if max_attempts <= 1:
            raise RuntimeError("workflow_intervention_invalid_output") from exc

        repair_system = load_prompt("json_repair_system.md")
        repair_user = render_prompt(
            load_prompt("json_repair_user.md"),
            {"INVALID_OUTPUT": raw_output or str(exc)},
        )
        repaired = await llm.complete(system_prompt=repair_system, user_prompt=repair_user)
        try:
            payload = extract_json_object(repaired)
            return WorkflowInterventionResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as repair_exc:
            raise RuntimeError("workflow_intervention_invalid_output") from repair_exc


async def build_workflow_intervention(
    *,
    llm: LLMClient,
    run_kind: str,
    run_status: str,
    run_state: dict[str, Any],
    instruction: str,
    target_step: dict[str, Any] | None = None,
    max_attempts: int = 2,
) -> WorkflowInterventionResult:
    system_prompt = load_prompt("workflow_intervention_system.md")
    user_prompt = render_prompt(
        load_prompt("workflow_intervention_user.md"),
        {
            "RUN_KIND": run_kind,
            "RUN_STATUS": run_status,
            "RUN_STATE_JSON": json.dumps(run_state or {}, ensure_ascii=False, indent=2),
            "TARGET_STEP_JSON": json.dumps(target_step or {}, ensure_ascii=False, indent=2)
            if target_step is not None
            else "(none)",
            "INSTRUCTION": instruction,
        },
    )

    raw = await llm.complete(system_prompt=system_prompt, user_prompt=user_prompt)
    return await parse_workflow_intervention_output(
        llm=llm,
        raw_output=raw,
        max_attempts=max_attempts,
    )

