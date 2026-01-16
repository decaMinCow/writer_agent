import { env } from '$env/dynamic/public';

const API_BASE = (env.PUBLIC_API_BASE_URL ?? 'http://localhost:9761').replace(/\/$/, '');

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${API_BASE}${path}`, {
		...init,
		headers: {
			'content-type': 'application/json',
			...(init?.headers ?? {}),
		},
	});

	if (!res.ok) {
		const text = await res.text().catch(() => '');
		throw new Error(`api_error ${res.status} ${path} ${text}`);
	}

	return (await res.json()) as T;
}

export type BriefRead = {
	id: string;
	title: string | null;
	content: Record<string, unknown>;
	created_at: string;
	updated_at: string;
};

export type ScriptFormat = 'screenplay_int_ext' | 'stage_play' | 'custom';

export type OutputSpecDefaults = {
	language: string;
	script_format: ScriptFormat;
	script_format_notes: string | null;
	max_fix_attempts: number;
	auto_step_retries: number;
	auto_step_backoff_s: number;
	[key: string]: unknown;
};

export type NovelToScriptPromptDefaults = {
	conversion_notes: string | null;
	[key: string]: unknown;
};

export type PromptPreset = {
	id: string;
	name: string;
	text: string;
	[key: string]: unknown;
};

export type PromptPresetCatalog = {
	default_preset_id: string | null;
	presets: PromptPreset[];
	[key: string]: unknown;
};

export type PromptPresets = {
	script: PromptPresetCatalog;
	novel_to_script: PromptPresetCatalog;
	[key: string]: unknown;
};

export type LlmProviderSettings = {
	base_url: string | null;
	model: string;
	embeddings_model: string;
	timeout_s: number;
	max_retries: number;
	api_key_configured: boolean;
	[key: string]: unknown;
};

export type LicenseStatus = {
	enabled: boolean;
	authorized: boolean;
	machine_code: string;
	license: Record<string, unknown> | null;
	error: string | null;
};

export type BriefSnapshotRead = {
	id: string;
	brief_id: string;
	label: string | null;
	content: Record<string, unknown>;
	created_at: string;
};

export type WorkflowRunRead = {
	id: string;
	kind: 'novel' | 'script' | 'novel_to_script';
	status: 'queued' | 'running' | 'paused' | 'succeeded' | 'failed' | 'canceled';
	brief_snapshot_id: string;
	state: Record<string, unknown>;
	error: Record<string, unknown> | null;
	created_at: string;
	updated_at: string;
};

export type WorkflowStepRunRead = {
	id: string;
	workflow_run_id: string;
	step_name: string;
	step_index: number | null;
	status: WorkflowRunRead['status'];
	outputs: Record<string, unknown>;
	error: string | null;
	started_at: string | null;
	finished_at: string | null;
	created_at: string;
	updated_at: string;
};

export type ArtifactRead = {
	id: string;
	kind: 'novel_chapter' | 'script_scene';
	title: string | null;
	ordinal: number | null;
	created_at: string;
	updated_at: string;
};

export type ArtifactVersionRead = {
	id: string;
	artifact_id: string;
	source: 'user' | 'agent';
	content_text: string;
	metadata: Record<string, unknown>;
	workflow_run_id: string | null;
	brief_snapshot_id: string | null;
	created_at: string;
};

export type KgEntityRead = {
	id: string;
	brief_snapshot_id: string;
	name: string;
	entity_type: string;
	metadata: Record<string, unknown>;
	created_at: string;
};

export type KgRelationRead = {
	id: string;
	brief_snapshot_id: string;
	subject_entity_id: string;
	predicate: string;
	object_entity_id: string;
	metadata: Record<string, unknown>;
	created_at: string;
};

export type KgEventRead = {
	id: string;
	brief_snapshot_id: string;
	event_key: string | null;
	summary: string;
	time_hint: string | null;
	artifact_version_id: string | null;
	metadata: Record<string, unknown>;
	created_at: string;
};

export type KnowledgeGraphRead = {
	entities: KgEntityRead[];
	relations: KgRelationRead[];
	events: KgEventRead[];
};

export type KnowledgeGraphRebuildResponse = {
	entities_indexed: number;
	relations_indexed: number;
	events_indexed: number;
};

export type LintIssueRead = {
	id: string;
	brief_snapshot_id: string;
	severity: 'hard' | 'soft' | string;
	code: string;
	message: string;
	artifact_version_id: string | null;
	metadata: Record<string, unknown>;
	created_at: string;
};

export type LintRunResponse = {
	issues: LintIssueRead[];
};

export type PropagationPreviewRequest = {
	base_artifact_version_id: string;
	edited_artifact_version_id: string;
};

export type ImpactReportItem = {
	artifact_id: string;
	artifact_version_id: string;
	kind: ArtifactRead['kind'];
	ordinal: number | null;
	title: string | null;
	reason: string;
};

export type PropagationPreviewResponse = {
	fact_changes: string;
	impacts: ImpactReportItem[];
	patches: Record<string, unknown>;
};

export type PropagationEventRead = {
	id: string;
	brief_snapshot_id: string;
	base_artifact_version_id: string;
	edited_artifact_version_id: string;
	fact_changes: string;
	metadata: Record<string, unknown>;
	created_at: string;
};

export type ArtifactImpactRead = {
	id: string;
	propagation_event_id: string;
	brief_snapshot_id: string;
	artifact_id: string;
	artifact_version_id: string;
	reason: string;
	repaired_artifact_version_id: string | null;
	repaired_at: string | null;
	created_at: string;
};

export type PropagationApplyResponse = {
	event: PropagationEventRead;
	impacts: ArtifactImpactRead[];
};

export type PropagationRepairResponse = {
	repaired: { artifact_id: string; artifact_version_id: string }[];
	impacts: ArtifactImpactRead[];
};

export async function listBriefs(): Promise<BriefRead[]> {
	return await fetchJson<BriefRead[]>('/api/briefs');
}

export async function createBrief(payload: {
	title?: string | null;
	content?: Record<string, unknown>;
}): Promise<BriefRead> {
	return await fetchJson<BriefRead>('/api/briefs', {
		method: 'POST',
		body: JSON.stringify({ title: payload.title ?? null, content: payload.content ?? {} }),
	});
}

export async function listBriefSnapshots(briefId: string): Promise<BriefSnapshotRead[]> {
	return await fetchJson<BriefSnapshotRead[]>(`/api/briefs/${briefId}/snapshots`);
}

export async function deleteBrief(briefId: string): Promise<{ deleted: boolean }> {
	return await fetchJson<{ deleted: boolean }>(`/api/briefs/${briefId}`, { method: 'DELETE' });
}

export async function deleteBriefSnapshot(snapshotId: string): Promise<{ deleted: boolean }> {
	return await fetchJson<{ deleted: boolean }>(`/api/brief-snapshots/${snapshotId}`, {
		method: 'DELETE',
	});
}

export async function createBriefSnapshot(
	briefId: string,
	payload: { label?: string | null },
): Promise<BriefSnapshotRead> {
	return await fetchJson<BriefSnapshotRead>(`/api/briefs/${briefId}/snapshots`, {
		method: 'POST',
		body: JSON.stringify({ label: payload.label ?? null }),
	});
}

export async function getGlobalOutputSpecDefaults(): Promise<OutputSpecDefaults> {
	return await fetchJson<OutputSpecDefaults>('/api/settings/output-spec');
}

export async function patchGlobalOutputSpecDefaults(payload: {
	language?: string | null;
	script_format?: ScriptFormat | null;
	script_format_notes?: string | null;
	max_fix_attempts?: number | null;
	auto_step_retries?: number | null;
	auto_step_backoff_s?: number | null;
}): Promise<OutputSpecDefaults> {
	return await fetchJson<OutputSpecDefaults>('/api/settings/output-spec', {
		method: 'PATCH',
		body: JSON.stringify(payload),
	});
}

export async function getNovelToScriptPromptDefaults(): Promise<NovelToScriptPromptDefaults> {
	return await fetchJson<NovelToScriptPromptDefaults>('/api/settings/novel-to-script-prompt');
}

export async function patchNovelToScriptPromptDefaults(payload: {
	conversion_notes?: string | null;
}): Promise<NovelToScriptPromptDefaults> {
	return await fetchJson<NovelToScriptPromptDefaults>('/api/settings/novel-to-script-prompt', {
		method: 'PATCH',
		body: JSON.stringify(payload),
	});
}

export async function getPromptPresets(): Promise<PromptPresets> {
	return await fetchJson<PromptPresets>('/api/settings/prompt-presets');
}

export async function patchPromptPresets(payload: {
	script?: PromptPresetCatalog | null;
	novel_to_script?: PromptPresetCatalog | null;
}): Promise<PromptPresets> {
	return await fetchJson<PromptPresets>('/api/settings/prompt-presets', {
		method: 'PATCH',
		body: JSON.stringify(payload),
	});
}

export async function getLlmProviderSettings(): Promise<LlmProviderSettings> {
	return await fetchJson<LlmProviderSettings>('/api/settings/llm-provider');
}

export async function patchLlmProviderSettings(payload: {
	base_url?: string | null;
	model?: string | null;
	embeddings_model?: string | null;
	timeout_s?: number | null;
	max_retries?: number | null;
	api_key?: string | null;
}): Promise<LlmProviderSettings> {
	return await fetchJson<LlmProviderSettings>('/api/settings/llm-provider', {
		method: 'PATCH',
		body: JSON.stringify(payload),
	});
}

export async function getLicenseStatus(): Promise<LicenseStatus> {
	return await fetchJson<LicenseStatus>('/api/license/status');
}

export async function activateLicense(licenseCode: string): Promise<LicenseStatus> {
	return await fetchJson<LicenseStatus>('/api/license/activate', {
		method: 'POST',
		body: JSON.stringify({ license_code: licenseCode }),
	});
}

export async function clearLicense(): Promise<LicenseStatus> {
	return await fetchJson<LicenseStatus>('/api/license/clear', {
		method: 'POST',
	});
}

export type BriefMessageRead = {
	id: string;
	brief_id: string;
	role: 'user' | 'assistant' | 'system';
	content_text: string;
	metadata: Record<string, unknown>;
	created_at: string;
};

export type GapReport = {
	mode: WorkflowRunRead['kind'];
	confirmed: string[];
	pending: string[];
	missing: string[];
	conflict: string[];
	questions: string[];
	completeness: number;
};

export type BriefMessageCreateResponse = {
	brief: BriefRead;
	gap_report: GapReport;
	messages: BriefMessageRead[];
};

export async function listBriefMessages(briefId: string): Promise<BriefMessageRead[]> {
	return await fetchJson<BriefMessageRead[]>(`/api/briefs/${briefId}/messages`);
}

export async function postBriefMessage(
	briefId: string,
	payload: { content_text: string; mode?: GapReport['mode'] },
): Promise<BriefMessageCreateResponse> {
	return await fetchJson<BriefMessageCreateResponse>(`/api/briefs/${briefId}/messages`, {
		method: 'POST',
		body: JSON.stringify(payload),
	});
}

type SseEvent = { event: string; data: unknown };

function parseSseEvent(raw: string): SseEvent | null {
	const lines = raw.split('\n').filter((line) => line.length > 0);
	if (lines.length === 0) return null;

	let event = 'message';
	const dataLines: string[] = [];
	for (const line of lines) {
		if (line.startsWith('event:')) {
			event = line.slice('event:'.length).trim();
		} else if (line.startsWith('data:')) {
			dataLines.push(line.slice('data:'.length).trimStart());
		}
	}

	const dataRaw = dataLines.join('\n');
	let data: unknown = dataRaw;
	if (dataRaw.length > 0) {
		try {
			data = JSON.parse(dataRaw) as unknown;
		} catch {
			data = dataRaw;
		}
	}

	return { event, data };
}

export async function streamBriefMessage(
	briefId: string,
	payload: { content_text: string; mode?: GapReport['mode'] },
	handlers: {
		onAssistantDelta?: (append: string) => void;
		onFinal?: (resp: BriefMessageCreateResponse) => void;
		onError?: (detail: string) => void;
		signal?: AbortSignal;
	} = {},
): Promise<void> {
	const res = await fetch(`${API_BASE}/api/briefs/${briefId}/messages/stream`, {
		method: 'POST',
		body: JSON.stringify(payload),
		signal: handlers.signal,
		headers: {
			accept: 'text/event-stream',
			'content-type': 'application/json',
		},
	});

	if (!res.ok) {
		const text = await res.text().catch(() => '');
		throw new Error(`api_error ${res.status} /api/briefs/${briefId}/messages/stream ${text}`);
	}
	if (!res.body) {
		throw new Error('api_error_stream_no_body');
	}

	const reader = res.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';

	while (true) {
		const { value, done } = await reader.read();
		if (done) break;

		buffer += decoder.decode(value, { stream: true });
		buffer = buffer.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

		while (true) {
			const sep = buffer.indexOf('\n\n');
			if (sep === -1) break;
			const rawEvent = buffer.slice(0, sep);
			buffer = buffer.slice(sep + 2);

			const evt = parseSseEvent(rawEvent);
			if (!evt) continue;

			if (evt.event === 'assistant_delta') {
				const append = (evt.data as any)?.append;
				if (typeof append === 'string' && append.length > 0) handlers.onAssistantDelta?.(append);
				continue;
			}
			if (evt.event === 'status') {
				// Optional: UI may use this to show "thinking..." state.
				continue;
			}
			if (evt.event === 'final') {
				handlers.onFinal?.(evt.data as BriefMessageCreateResponse);
				try {
					await reader.cancel();
				} catch {
					// ignore
				}
				return;
			}
			if (evt.event === 'error') {
				const detail = (evt.data as any)?.detail;
				const message = typeof detail === 'string' ? detail : 'stream_error';
				handlers.onError?.(message);
				throw new Error(message);
			}
		}
	}
}

export async function listWorkflowRuns(briefSnapshotId?: string): Promise<WorkflowRunRead[]> {
	const qs = briefSnapshotId ? `?brief_snapshot_id=${encodeURIComponent(briefSnapshotId)}` : '';
	return await fetchJson<WorkflowRunRead[]>(`/api/workflow-runs${qs}`);
}

export async function deleteWorkflowRun(runId: string): Promise<{ deleted: boolean }> {
	return await fetchJson<{ deleted: boolean }>(`/api/workflow-runs/${runId}`, { method: 'DELETE' });
}

export async function listWorkflowSteps(runId: string): Promise<WorkflowStepRunRead[]> {
	return await fetchJson<WorkflowStepRunRead[]>(`/api/workflow-runs/${runId}/steps`);
}

export type WorkflowInterventionResponse = {
	run: WorkflowRunRead;
	step: WorkflowStepRunRead;
	assistant_message: string;
	state_patch: Record<string, unknown>;
};

export async function applyWorkflowIntervention(
	runId: string,
	payload: { instruction: string; step_id?: string | null },
): Promise<WorkflowInterventionResponse> {
	return await fetchJson<WorkflowInterventionResponse>(`/api/workflow-runs/${runId}/interventions`, {
		method: 'POST',
		body: JSON.stringify({ instruction: payload.instruction, step_id: payload.step_id ?? null }),
	});
}

export type WorkflowNextResponse = {
	run: WorkflowRunRead;
	step: WorkflowStepRunRead;
};

export type WorkflowControlResponse = {
	run: WorkflowRunRead;
};

export async function createWorkflowRun(payload: {
	kind: WorkflowRunRead['kind'];
	brief_snapshot_id: string;
	source_brief_snapshot_id?: string | null;
	prompt_preset_id?: string | null;
	split_mode?: 'chapter_unit' | 'auto_by_length' | null;
	conversion_output_spec?:
		| {
				script_format?: ScriptFormat | null;
				script_format_notes?: string | null;
		  }
		| null;
	state?: Record<string, unknown>;
}): Promise<WorkflowRunRead> {
	return await fetchJson<WorkflowRunRead>('/api/workflow-runs', {
		method: 'POST',
		body: JSON.stringify({
			kind: payload.kind,
			brief_snapshot_id: payload.brief_snapshot_id,
			source_brief_snapshot_id: payload.source_brief_snapshot_id ?? null,
			prompt_preset_id: payload.prompt_preset_id ?? null,
			split_mode: payload.split_mode ?? null,
			conversion_output_spec: payload.conversion_output_spec ?? null,
			state: payload.state ?? {},
		}),
	});
}

export async function executeWorkflowNext(runId: string): Promise<WorkflowNextResponse> {
	return await fetchJson<WorkflowNextResponse>(`/api/workflow-runs/${runId}/next`, {
		method: 'POST',
	});
}

export async function patchWorkflowRun(
	runId: string,
	payload: {
		status?: WorkflowRunRead['status'] | null;
		state?: Record<string, unknown> | null;
		error?: Record<string, unknown> | null;
	},
): Promise<WorkflowRunRead> {
	return await fetchJson<WorkflowRunRead>(`/api/workflow-runs/${runId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload),
	});
}

export async function forkWorkflowRun(
	runId: string,
	payload?: { step_id?: string | null; state?: Record<string, unknown> | null },
): Promise<WorkflowRunRead> {
	return await fetchJson<WorkflowRunRead>(`/api/workflow-runs/${runId}/fork`, {
		method: 'POST',
		body: JSON.stringify({ step_id: payload?.step_id ?? null, state: payload?.state ?? null }),
	});
}

export async function startWorkflowAutorun(runId: string): Promise<WorkflowControlResponse> {
	return await fetchJson<WorkflowControlResponse>(`/api/workflow-runs/${runId}/autorun/start`, {
		method: 'POST',
	});
}

export async function stopWorkflowAutorun(runId: string): Promise<WorkflowControlResponse> {
	return await fetchJson<WorkflowControlResponse>(`/api/workflow-runs/${runId}/autorun/stop`, {
		method: 'POST',
	});
}

export function workflowRunEventsUrl(runId: string): string {
	return `${API_BASE}/api/workflow-runs/${runId}/events`;
}

export async function pauseWorkflowRun(runId: string): Promise<WorkflowControlResponse> {
	return await fetchJson<WorkflowControlResponse>(`/api/workflow-runs/${runId}/pause`, {
		method: 'POST',
	});
}

export async function resumeWorkflowRun(runId: string): Promise<WorkflowControlResponse> {
	return await fetchJson<WorkflowControlResponse>(`/api/workflow-runs/${runId}/resume`, {
		method: 'POST',
	});
}

export async function listArtifacts(payload?: { brief_snapshot_id?: string | null }): Promise<ArtifactRead[]> {
	const snapshotId = payload?.brief_snapshot_id ?? null;
	const qs = snapshotId ? `?brief_snapshot_id=${encodeURIComponent(snapshotId)}` : '';
	return await fetchJson<ArtifactRead[]>(`/api/artifacts${qs}`);
}

export async function listArtifactVersions(
	artifactId: string,
	payload?: { brief_snapshot_id?: string | null },
): Promise<ArtifactVersionRead[]> {
	const snapshotId = payload?.brief_snapshot_id ?? null;
	const qs = snapshotId ? `?brief_snapshot_id=${encodeURIComponent(snapshotId)}` : '';
	return await fetchJson<ArtifactVersionRead[]>(`/api/artifacts/${artifactId}/versions${qs}`);
}

export async function getArtifactVersion(versionId: string): Promise<ArtifactVersionRead> {
	return await fetchJson<ArtifactVersionRead>(`/api/artifacts/versions/${versionId}`);
}

export async function createArtifactVersion(
	artifactId: string,
	payload: {
		source?: ArtifactVersionRead['source'];
		content_text: string;
		metadata?: Record<string, unknown>;
		workflow_run_id?: string | null;
		brief_snapshot_id?: string | null;
	},
): Promise<ArtifactVersionRead> {
	return await fetchJson<ArtifactVersionRead>(`/api/artifacts/${artifactId}/versions`, {
		method: 'POST',
		body: JSON.stringify({
			source: payload.source ?? 'user',
			content_text: payload.content_text,
			metadata: payload.metadata ?? {},
			workflow_run_id: payload.workflow_run_id ?? null,
			brief_snapshot_id: payload.brief_snapshot_id ?? null,
		}),
	});
}

export async function rewriteArtifactVersion(
	versionId: string,
	payload: { instruction: string; selection_start?: number | null; selection_end?: number | null },
): Promise<ArtifactVersionRead> {
	return await fetchJson<ArtifactVersionRead>(`/api/artifacts/versions/${versionId}/rewrite`, {
		method: 'POST',
		body: JSON.stringify({
			instruction: payload.instruction,
			selection_start: payload.selection_start ?? null,
			selection_end: payload.selection_end ?? null,
		}),
	});
}

export async function getKnowledgeGraph(snapshotId: string): Promise<KnowledgeGraphRead> {
	return await fetchJson<KnowledgeGraphRead>(`/api/brief-snapshots/${snapshotId}/kg`);
}

export async function rebuildKnowledgeGraph(
	snapshotId: string,
): Promise<KnowledgeGraphRebuildResponse> {
	return await fetchJson<KnowledgeGraphRebuildResponse>(
		`/api/brief-snapshots/${snapshotId}/kg/rebuild`,
		{
			method: 'POST',
		},
	);
}

export async function listLintIssues(snapshotId: string): Promise<LintIssueRead[]> {
	return await fetchJson<LintIssueRead[]>(`/api/brief-snapshots/${snapshotId}/lint`);
}

export async function runStoryLint(
	snapshotId: string,
	payload?: { use_llm?: boolean },
): Promise<LintRunResponse> {
	const use_llm = payload?.use_llm ?? true;
	return await fetchJson<LintRunResponse>(
		`/api/brief-snapshots/${snapshotId}/lint?use_llm=${encodeURIComponent(String(use_llm))}`,
		{ method: 'POST' },
	);
}

export async function listImpacts(
	snapshotId: string,
	payload?: { include_repaired?: boolean },
): Promise<ArtifactImpactRead[]> {
	const include_repaired = payload?.include_repaired ?? false;
	return await fetchJson<ArtifactImpactRead[]>(
		`/api/brief-snapshots/${snapshotId}/impacts?include_repaired=${encodeURIComponent(
			String(include_repaired),
		)}`,
	);
}

export async function previewPropagation(
	snapshotId: string,
	payload: PropagationPreviewRequest,
	options?: { use_llm?: boolean },
): Promise<PropagationPreviewResponse> {
	const use_llm = options?.use_llm ?? false;
	return await fetchJson<PropagationPreviewResponse>(
		`/api/brief-snapshots/${snapshotId}/propagation/preview?use_llm=${encodeURIComponent(
			String(use_llm),
		)}`,
		{ method: 'POST', body: JSON.stringify(payload) },
	);
}

export async function applyPropagation(
	snapshotId: string,
	payload: PropagationPreviewRequest,
	options?: { use_llm?: boolean },
): Promise<PropagationApplyResponse> {
	const use_llm = options?.use_llm ?? false;
	return await fetchJson<PropagationApplyResponse>(
		`/api/brief-snapshots/${snapshotId}/propagation/apply?use_llm=${encodeURIComponent(
			String(use_llm),
		)}`,
		{ method: 'POST', body: JSON.stringify(payload) },
	);
}

export async function repairPropagation(
	snapshotId: string,
	eventId: string,
	payload?: { artifact_ids?: string[] },
): Promise<PropagationRepairResponse> {
	return await fetchJson<PropagationRepairResponse>(
		`/api/brief-snapshots/${snapshotId}/propagation/events/${eventId}/repair`,
		{
			method: 'POST',
			body: JSON.stringify({ artifact_ids: payload?.artifact_ids ?? null }),
		},
	);
}

export type OpenThreadRead = {
	id: string;
	brief_snapshot_id: string;
	title: string;
	description: string | null;
	status: string;
	metadata: Record<string, unknown>;
	created_at: string;
	updated_at: string;
};

export type OpenThreadRefRead = {
	id: string;
	thread_id: string;
	artifact_version_id: string;
	ref_kind: string;
	quote: string | null;
	metadata: Record<string, unknown>;
	created_at: string;
};

export async function listOpenThreads(
	snapshotId: string,
	payload?: { status?: string | null },
): Promise<OpenThreadRead[]> {
	const status = payload?.status ?? null;
	const qs = status ? `?status=${encodeURIComponent(status)}` : '';
	return await fetchJson<OpenThreadRead[]>(`/api/brief-snapshots/${snapshotId}/threads${qs}`);
}

export async function createOpenThread(
	snapshotId: string,
	payload: {
		title: string;
		description?: string | null;
		status?: string;
		metadata?: Record<string, unknown>;
	},
): Promise<OpenThreadRead> {
	return await fetchJson<OpenThreadRead>(`/api/brief-snapshots/${snapshotId}/threads`, {
		method: 'POST',
		body: JSON.stringify({
			title: payload.title,
			description: payload.description ?? null,
			status: payload.status ?? 'open',
			metadata: payload.metadata ?? {},
		}),
	});
}

export async function updateOpenThread(
	snapshotId: string,
	threadId: string,
	payload: {
		title?: string | null;
		description?: string | null;
		status?: string | null;
		metadata?: Record<string, unknown> | null;
	},
): Promise<OpenThreadRead> {
	return await fetchJson<OpenThreadRead>(`/api/brief-snapshots/${snapshotId}/threads/${threadId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload),
	});
}

export async function listOpenThreadRefs(
	snapshotId: string,
	threadId: string,
): Promise<OpenThreadRefRead[]> {
	return await fetchJson<OpenThreadRefRead[]>(
		`/api/brief-snapshots/${snapshotId}/threads/${threadId}/refs`,
	);
}

export async function createOpenThreadRef(
	snapshotId: string,
	threadId: string,
	payload: {
		artifact_version_id: string;
		ref_kind?: string;
		quote?: string | null;
		metadata?: Record<string, unknown>;
	},
): Promise<OpenThreadRefRead> {
	return await fetchJson<OpenThreadRefRead>(
		`/api/brief-snapshots/${snapshotId}/threads/${threadId}/refs`,
		{
			method: 'POST',
			body: JSON.stringify({
				artifact_version_id: payload.artifact_version_id,
				ref_kind: payload.ref_kind ?? 'introduced',
				quote: payload.quote ?? null,
				metadata: payload.metadata ?? {},
			}),
		},
	);
}

export type GlossaryEntryRead = {
	id: string;
	brief_snapshot_id: string;
	term: string;
	replacement: string;
	metadata: Record<string, unknown>;
	created_at: string;
	updated_at: string;
};

export async function listGlossaryEntries(snapshotId: string): Promise<GlossaryEntryRead[]> {
	return await fetchJson<GlossaryEntryRead[]>(`/api/brief-snapshots/${snapshotId}/glossary`);
}

export async function createGlossaryEntry(
	snapshotId: string,
	payload: { term: string; replacement: string; metadata?: Record<string, unknown> },
): Promise<GlossaryEntryRead> {
	return await fetchJson<GlossaryEntryRead>(`/api/brief-snapshots/${snapshotId}/glossary`, {
		method: 'POST',
		body: JSON.stringify({
			term: payload.term,
			replacement: payload.replacement,
			metadata: payload.metadata ?? {},
		}),
	});
}

export type ExportResponse = {
	filename: string;
	content_type: string;
	text: string;
};

export async function exportNovelMarkdown(
	snapshotId: string,
	payload?: { apply_glossary?: boolean },
): Promise<ExportResponse> {
	const apply_glossary = payload?.apply_glossary ?? true;
	return await fetchJson<ExportResponse>(
		`/api/brief-snapshots/${snapshotId}/export/novel.md?apply_glossary=${encodeURIComponent(
			String(apply_glossary),
		)}`,
	);
}

export async function exportNovelText(
	snapshotId: string,
	payload?: { apply_glossary?: boolean },
): Promise<ExportResponse> {
	const apply_glossary = payload?.apply_glossary ?? true;
	return await fetchJson<ExportResponse>(
		`/api/brief-snapshots/${snapshotId}/export/novel.txt?apply_glossary=${encodeURIComponent(
			String(apply_glossary),
		)}`,
	);
}

export async function exportScriptFountain(
	snapshotId: string,
	payload?: { apply_glossary?: boolean },
): Promise<ExportResponse> {
	const apply_glossary = payload?.apply_glossary ?? true;
	return await fetchJson<ExportResponse>(
		`/api/brief-snapshots/${snapshotId}/export/script.fountain?apply_glossary=${encodeURIComponent(
			String(apply_glossary),
		)}`,
	);
}

export async function exportScriptText(
	snapshotId: string,
	payload?: { apply_glossary?: boolean },
): Promise<ExportResponse> {
	const apply_glossary = payload?.apply_glossary ?? true;
	return await fetchJson<ExportResponse>(
		`/api/brief-snapshots/${snapshotId}/export/script.txt?apply_glossary=${encodeURIComponent(
			String(apply_glossary),
		)}`,
	);
}
