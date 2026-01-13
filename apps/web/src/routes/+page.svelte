<script lang="ts">
	import { onDestroy, onMount, tick } from 'svelte';
	import {
		applyPropagation,
		createWorkflowRun,
		createBrief,
		createBriefSnapshot,
		deleteBrief,
		deleteBriefSnapshot,
		previewPropagation,
		repairPropagation,
		createOpenThread,
		createOpenThreadRef,
		forkWorkflowRun,
		getArtifactVersion,
		getGlobalOutputSpecDefaults,
		getLlmProviderSettings,
		getKnowledgeGraph,
		createArtifactVersion,
		createGlossaryEntry,
		listArtifacts,
		listArtifactVersions,
		listBriefMessages,
		listBriefSnapshots,
		listBriefs,
		listGlossaryEntries,
		listLintIssues,
		listOpenThreadRefs,
		listOpenThreads,
		exportNovelMarkdown,
		exportNovelText,
		exportScriptFountain,
		updateOpenThread,
		patchBriefOutputSpecOverrides,
		patchGlobalOutputSpecDefaults,
		patchLlmProviderSettings,
		streamBriefMessage,
		rebuildKnowledgeGraph,
		executeWorkflowNext,
		runStoryLint,
		startWorkflowAutorun,
		stopWorkflowAutorun,
		workflowRunEventsUrl,
		listWorkflowRuns,
		deleteWorkflowRun,
		listWorkflowSteps,
		pauseWorkflowRun,
		patchWorkflowRun,
		applyWorkflowIntervention,
		resumeWorkflowRun,
		rewriteArtifactVersion,
		type WorkflowInterventionResponse,
		type ArtifactRead,
		type ArtifactImpactRead,
		type ArtifactVersionRead,
		type BriefRead,
		type BriefMessageRead,
		type BriefSnapshotRead,
		type GapReport,
		type KnowledgeGraphRead,
		type LintIssueRead,
		type OpenThreadRead,
		type OpenThreadRefRead,
		type PropagationEventRead,
		type PropagationPreviewResponse,
		type GlossaryEntryRead,
		type OutputSpecDefaults,
		type LlmProviderSettings,
		type ScriptFormat,
		type WorkflowRunRead,
		type WorkflowStepRunRead,
	} from '$lib/api';

	let error: string | null = null;

	let briefs: BriefRead[] = [];
	let selectedBrief: BriefRead | null = null;
	let briefSnapshots: BriefSnapshotRead[] = [];
	let selectedSnapshot: BriefSnapshotRead | null = null;
	let briefMessages: BriefMessageRead[] = [];
	let gapReport: GapReport | null = null;
	let messageDraft = '';
	let selectedMode: GapReport['mode'] = 'novel';
	let sendingMessage = false;
	let messageTextarea: HTMLTextAreaElement | null = null;

	let globalOutputSpec: OutputSpecDefaults | null = null;
	let globalLanguageDraft = 'zh-CN';
	let globalScriptFormatDraft: ScriptFormat = 'screenplay_int_ext';
	let globalScriptNotesDraft = '';
	let globalMaxFixAttemptsDraft = '2';
	let savingGlobalPrefs = false;

	let llmProviderSettings: LlmProviderSettings | null = null;
	let providerBaseUrlDraft = '';
	let providerModelDraft = '';
	let providerEmbeddingsModelDraft = '';
	let providerTimeoutDraft = '60';
	let providerMaxRetriesDraft = '2';
	let providerApiKeyDraft = '';
	let savingProviderSettings = false;

	let newBriefTitle = '';
	let creatingBrief = false;
	let newSnapshotLabel = '';
	let creatingSnapshot = false;

	let overrideLanguage = false;
	let overrideScriptFormat = false;
	let overrideScriptNotes = false;
	let overrideMaxFixAttempts = false;
	let briefLanguageDraft = 'zh-CN';
	let briefScriptFormatDraft: ScriptFormat = 'screenplay_int_ext';
	let briefScriptNotesDraft = '';
	let briefMaxFixAttemptsDraft = '2';
	let savingBriefPrefs = false;
	let showBriefJson = false;
	let showSnapshotJson = false;

	let workflowRuns: WorkflowRunRead[] = [];
	let visibleWorkflowRuns: WorkflowRunRead[] = [];
	let selectedRun: WorkflowRunRead | null = null;
	let workflowSteps: WorkflowStepRunRead[] = [];
	let selectedStep: WorkflowStepRunRead | null = null;
	let workflowKindDraft: WorkflowRunRead['kind'] = 'novel';
	let creatingRun = false;
	let stepping = false;
	let autoRunning = false;
	let runEvents: EventSource | null = null;
	let runStateDraft = '';
	let savingRunState = false;
	let forkingRun = false;

	let interventionDraft = '';
	let sendingIntervention = false;
	let interventionTextarea: HTMLTextAreaElement | null = null;
	let interventionSteps: WorkflowStepRunRead[] = [];
	let lastFailedStep: WorkflowStepRunRead | null = null;
	let llmStreamByStep: Record<string, string> = {};

	let artifacts: ArtifactRead[] = [];
	let selectedArtifact: ArtifactRead | null = null;
	let artifactVersions: ArtifactVersionRead[] = [];
	let selectedArtifactVersion: ArtifactVersionRead | null = null;
	let artifactEditorDraft = '';
	let savingArtifactVersion = false;
	let artifactTextarea: HTMLTextAreaElement | null = null;
	let rewriteInstructionDraft = '';
	let rewriteSelectionStart: number | null = null;
	let rewriteSelectionEnd: number | null = null;
	let rewritingSelection = false;

	let propagationPreview: PropagationPreviewResponse | null = null;
	let propagationBaseVersionId: string | null = null;
	let propagationEditedVersionId: string | null = null;
	let propagationEvent: PropagationEventRead | null = null;
	let propagationImpacts: ArtifactImpactRead[] = [];
	let previewingPropagation = false;
	let repairingPropagation = false;

	let knowledgeGraph: KnowledgeGraphRead | null = null;
	let lintIssues: LintIssueRead[] = [];
	let openThreads: OpenThreadRead[] = [];
	let selectedOpenThread: OpenThreadRead | null = null;
	let openThreadRefs: OpenThreadRefRead[] = [];
	let newThreadTitleDraft = '';
	let newThreadDescriptionDraft = '';
	let creatingThread = false;
	let refArtifactVersionIdDraft = '';
	let refKindDraft = 'introduced';
	let refQuoteDraft = '';
	let addingThreadRef = false;
	let glossaryEntries: GlossaryEntryRead[] = [];
	let glossaryTermDraft = '';
	let glossaryReplacementDraft = '';
	let creatingGlossaryEntry = false;
	let applyGlossaryOnExport = true;
	let exportingNovelMd = false;
	let exportingNovelTxt = false;
	let exportingScriptFountain = false;
	let loadingAnalysis = false;
	let rebuildingKg = false;
	let runningLint = false;
	let lintUseLlm = true;

	function tempId(prefix: string): string {
		const uuid =
			typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
				? crypto.randomUUID()
				: String(Date.now() + Math.random());
		return `${prefix}-${uuid}`;
	}

	function autosizeMessageTextarea() {
		if (!messageTextarea) return;
		messageTextarea.style.height = 'auto';
		messageTextarea.style.height = `${messageTextarea.scrollHeight}px`;
	}

	function autosizeInterventionTextarea() {
		if (!interventionTextarea) return;
		interventionTextarea.style.height = 'auto';
		interventionTextarea.style.height = `${interventionTextarea.scrollHeight}px`;
	}

	function clearPropagation() {
		propagationPreview = null;
		propagationBaseVersionId = null;
		propagationEditedVersionId = null;
		propagationEvent = null;
		propagationImpacts = [];
	}

	function readBriefOutputSpecOverrides(brief: BriefRead | null): Record<string, unknown> {
		const content = brief?.content;
		if (!content || typeof content !== 'object') return {};
		const output = (content as any).output_spec;
		if (!output || typeof output !== 'object') return {};
		return output as Record<string, unknown>;
	}

	function hasOwn(obj: Record<string, unknown>, key: string): boolean {
		return Object.prototype.hasOwnProperty.call(obj, key);
	}

	function effectiveOutputSpec(): OutputSpecDefaults | null {
		if (!globalOutputSpec) return null;
		const overrides = readBriefOutputSpecOverrides(selectedBrief);

		const merged: OutputSpecDefaults = { ...globalOutputSpec };
		if (hasOwn(overrides, 'language') && typeof overrides.language === 'string') {
			merged.language = overrides.language;
		}
		if (hasOwn(overrides, 'script_format') && typeof overrides.script_format === 'string') {
			merged.script_format = overrides.script_format as ScriptFormat;
		}
		if (hasOwn(overrides, 'script_format_notes')) {
			const v = overrides.script_format_notes;
			merged.script_format_notes =
				v === null || typeof v === 'string' ? (v as any) : merged.script_format_notes;
		}
		if (hasOwn(overrides, 'max_fix_attempts')) {
			const v = (overrides as any).max_fix_attempts;
			const parsed =
				typeof v === 'number' ? v : typeof v === 'string' ? Number.parseInt(v, 10) : NaN;
			if (Number.isFinite(parsed) && parsed >= 0) merged.max_fix_attempts = parsed;
		}

		return merged;
	}

	function syncGlobalDrafts() {
		if (!globalOutputSpec) return;
		globalLanguageDraft = globalOutputSpec.language;
		globalScriptFormatDraft = globalOutputSpec.script_format;
		globalScriptNotesDraft = globalOutputSpec.script_format_notes ?? '';
		globalMaxFixAttemptsDraft = String(globalOutputSpec.max_fix_attempts ?? 2);
	}

	function syncProviderDrafts() {
		if (!llmProviderSettings) return;
		providerBaseUrlDraft = llmProviderSettings.base_url ?? '';
		providerModelDraft = llmProviderSettings.model ?? '';
		providerEmbeddingsModelDraft = llmProviderSettings.embeddings_model ?? '';
		providerTimeoutDraft =
			llmProviderSettings.timeout_s !== undefined && llmProviderSettings.timeout_s !== null
				? String(llmProviderSettings.timeout_s)
				: '60';
		providerMaxRetriesDraft = String(llmProviderSettings.max_retries ?? 2);
		providerApiKeyDraft = '';
	}

	function syncBriefOverrideDrafts() {
		if (!selectedBrief) return;
		const overrides = readBriefOutputSpecOverrides(selectedBrief);
		const effective = effectiveOutputSpec();

		overrideLanguage = hasOwn(overrides, 'language');
		overrideScriptFormat = hasOwn(overrides, 'script_format');
		overrideScriptNotes = hasOwn(overrides, 'script_format_notes');
		overrideMaxFixAttempts = hasOwn(overrides, 'max_fix_attempts');

		briefLanguageDraft = effective?.language ?? 'zh-CN';
		briefScriptFormatDraft = effective?.script_format ?? 'screenplay_int_ext';
		briefScriptNotesDraft = effective?.script_format_notes ?? '';
		briefMaxFixAttemptsDraft = String(effective?.max_fix_attempts ?? 2);

		if (overrideLanguage && typeof overrides.language === 'string') {
			briefLanguageDraft = overrides.language;
		}
		if (overrideScriptFormat && typeof overrides.script_format === 'string') {
			briefScriptFormatDraft = overrides.script_format as ScriptFormat;
		}
		if (overrideScriptNotes) {
			const v = overrides.script_format_notes;
			briefScriptNotesDraft = v === null ? '' : typeof v === 'string' ? v : '';
		}
		if (overrideMaxFixAttempts) {
			const v = (overrides as any).max_fix_attempts;
			const parsed =
				typeof v === 'number' ? v : typeof v === 'string' ? Number.parseInt(v, 10) : NaN;
			if (Number.isFinite(parsed) && parsed >= 0) briefMaxFixAttemptsDraft = String(parsed);
		}
	}

	async function refreshAll() {
		error = null;
		try {
			[briefs, workflowRuns, artifacts] = await Promise.all([
				listBriefs(),
				listWorkflowRuns(),
				listArtifacts(),
			]);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function refreshSettings() {
		error = null;
		try {
			globalOutputSpec = await getGlobalOutputSpecDefaults();
			syncGlobalDrafts();
			syncBriefOverrideDrafts();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function refreshProviderSettings() {
		error = null;
		try {
			llmProviderSettings = await getLlmProviderSettings();
			syncProviderDrafts();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function saveProviderSettings() {
		error = null;
		savingProviderSettings = true;
		try {
			const payload: {
				base_url?: string | null;
				model?: string | null;
				embeddings_model?: string | null;
				timeout_s?: number | null;
				max_retries?: number | null;
				api_key?: string | null;
			} = {
				base_url: providerBaseUrlDraft.trim() || null,
				model: providerModelDraft.trim() || null,
				embeddings_model: providerEmbeddingsModelDraft.trim() || null,
			};

			const timeout = Number(providerTimeoutDraft);
			payload.timeout_s = Number.isFinite(timeout) && timeout > 0 ? timeout : null;

			const maxRetries = Number(providerMaxRetriesDraft);
			payload.max_retries = Number.isFinite(maxRetries) && maxRetries >= 0 ? Math.floor(maxRetries) : null;

			const key = providerApiKeyDraft.trim();
			if (key) {
				payload.api_key = key;
			}

			llmProviderSettings = await patchLlmProviderSettings(payload);
			syncProviderDrafts();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			savingProviderSettings = false;
		}
	}

	async function clearProviderApiKey() {
		if (!llmProviderSettings?.api_key_configured) return;
		error = null;
		savingProviderSettings = true;
		try {
			llmProviderSettings = await patchLlmProviderSettings({ api_key: null });
			syncProviderDrafts();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			savingProviderSettings = false;
		}
	}

	async function selectBrief(brief: BriefRead) {
		closeRunEvents();
		autoRunning = false;
		selectedBrief = brief;
		showBriefJson = false;
		showSnapshotJson = false;
		selectedRun = null;
		selectedArtifact = null;
		selectedSnapshot = null;
		selectedStep = null;
		workflowSteps = [];
		artifactVersions = [];
		selectedArtifactVersion = null;
		artifactEditorDraft = '';
		clearPropagation();
		knowledgeGraph = null;
		lintIssues = [];
		openThreads = [];
		selectedOpenThread = null;
		openThreadRefs = [];
		glossaryEntries = [];
		try {
			[briefSnapshots, briefMessages] = await Promise.all([
				listBriefSnapshots(brief.id),
				listBriefMessages(brief.id),
			]);
			gapReport = null;
			syncBriefOverrideDrafts();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function selectRun(run: WorkflowRunRead) {
		closeRunEvents();
		autoRunning = false;
		selectedRun = run;
		runStateDraft = JSON.stringify(run.state, null, 2);
		llmStreamByStep = {};
		selectedArtifact = null;
		selectedStep = null;
		artifactVersions = [];
		selectedArtifactVersion = null;
		artifactEditorDraft = '';
		clearPropagation();
		try {
			workflowSteps = await listWorkflowSteps(run.id);
			subscribeToRunEvents(run.id);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function selectArtifact(artifact: ArtifactRead) {
		closeRunEvents();
		autoRunning = false;
		selectedArtifact = artifact;
		llmStreamByStep = {};
		selectedBrief = null;
		selectedRun = null;
		selectedSnapshot = null;
		selectedStep = null;
		briefSnapshots = [];
		briefMessages = [];
		gapReport = null;
		workflowSteps = [];
		selectedArtifactVersion = null;
		artifactEditorDraft = '';
		clearPropagation();
		knowledgeGraph = null;
		lintIssues = [];
		openThreads = [];
		selectedOpenThread = null;
		openThreadRefs = [];
		glossaryEntries = [];
		try {
			artifactVersions = await listArtifactVersions(artifact.id);
			if (artifactVersions.length > 0) {
				selectArtifactVersion(artifactVersions[0]);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	function selectArtifactVersion(v: ArtifactVersionRead) {
		selectedArtifactVersion = v;
		artifactEditorDraft = v.content_text;
		clearPropagation();
	}

	function resetArtifactDraft() {
		if (!selectedArtifactVersion) return;
		artifactEditorDraft = selectedArtifactVersion.content_text;
	}

	function captureRewriteSelection() {
		if (!artifactTextarea) return;
		rewriteSelectionStart = artifactTextarea.selectionStart;
		rewriteSelectionEnd = artifactTextarea.selectionEnd;
	}

	async function runTargetedRewrite() {
		if (!selectedArtifact || !selectedArtifactVersion) return;
		const instruction = rewriteInstructionDraft.trim();
		if (!instruction) return;
		if (rewriteSelectionStart === null || rewriteSelectionEnd === null) return;
		if (rewriteSelectionStart === rewriteSelectionEnd) return;

		error = null;
		rewritingSelection = true;
		try {
			const created = await rewriteArtifactVersion(selectedArtifactVersion.id, {
				instruction,
				selection_start: rewriteSelectionStart,
				selection_end: rewriteSelectionEnd,
			});
			artifactVersions = await listArtifactVersions(selectedArtifact.id);
			selectArtifactVersion(created);
			rewriteInstructionDraft = '';
			rewriteSelectionStart = null;
			rewriteSelectionEnd = null;
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			rewritingSelection = false;
		}
	}

	async function saveArtifactEdit() {
		if (!selectedArtifact || !selectedArtifactVersion) return;
		const text = artifactEditorDraft;
		if (!text.trim()) return;

		const baseVersionId = selectedArtifactVersion.id;
		const snapshotId = selectedArtifactVersion.brief_snapshot_id;

		error = null;
		savingArtifactVersion = true;
		try {
			const created = await createArtifactVersion(selectedArtifact.id, {
				source: 'user',
				content_text: text,
				brief_snapshot_id: selectedArtifactVersion.brief_snapshot_id,
				metadata: {
					edited_from_version_id: selectedArtifactVersion.id,
					edited_at: new Date().toISOString(),
				},
			});
			artifactVersions = await listArtifactVersions(selectedArtifact.id);
			selectArtifactVersion(created);
			if (snapshotId) {
				previewingPropagation = true;
				try {
					propagationPreview = await previewPropagation(snapshotId, {
						base_artifact_version_id: baseVersionId,
						edited_artifact_version_id: created.id,
					});
					propagationBaseVersionId = baseVersionId;
					propagationEditedVersionId = created.id;
				} finally {
					previewingPropagation = false;
				}
			}
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			savingArtifactVersion = false;
		}
	}

	async function applyAndRepairPropagation() {
		if (!selectedArtifactVersion?.brief_snapshot_id) return;
		if (!propagationBaseVersionId || !propagationEditedVersionId) return;

		const snapshotId = selectedArtifactVersion.brief_snapshot_id;

		error = null;
		repairingPropagation = true;
		try {
			const applied = await applyPropagation(snapshotId, {
				base_artifact_version_id: propagationBaseVersionId,
				edited_artifact_version_id: propagationEditedVersionId,
			});
			propagationEvent = applied.event;
			propagationImpacts = applied.impacts;

			const repaired = await repairPropagation(snapshotId, applied.event.id);
			propagationImpacts = repaired.impacts;

			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			repairingPropagation = false;
		}
	}

	async function refreshAnalysis() {
		if (!selectedSnapshot) return;
		error = null;
		loadingAnalysis = true;
		try {
			[knowledgeGraph, lintIssues, openThreads, glossaryEntries] = await Promise.all([
				getKnowledgeGraph(selectedSnapshot.id),
				listLintIssues(selectedSnapshot.id),
				listOpenThreads(selectedSnapshot.id),
				listGlossaryEntries(selectedSnapshot.id),
			]);
			selectedOpenThread = null;
			openThreadRefs = [];
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loadingAnalysis = false;
		}
	}

	async function rebuildKg() {
		if (!selectedSnapshot) return;
		error = null;
		rebuildingKg = true;
		try {
			await rebuildKnowledgeGraph(selectedSnapshot.id);
			knowledgeGraph = await getKnowledgeGraph(selectedSnapshot.id);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			rebuildingKg = false;
		}
	}

	async function runLint() {
		if (!selectedSnapshot) return;
		error = null;
		runningLint = true;
		try {
			const resp = await runStoryLint(selectedSnapshot.id, { use_llm: lintUseLlm });
			lintIssues = resp.issues;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			runningLint = false;
		}
	}

	async function refreshOpenThreadRefs() {
		if (!selectedSnapshot || !selectedOpenThread) return;
		error = null;
		try {
			openThreadRefs = await listOpenThreadRefs(selectedSnapshot.id, selectedOpenThread.id);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function selectOpenThread(thread: OpenThreadRead) {
		selectedOpenThread = thread;
		await refreshOpenThreadRefs();
	}

	async function createThread() {
		if (!selectedSnapshot) return;
		const title = newThreadTitleDraft.trim();
		if (!title) return;

		error = null;
		creatingThread = true;
		try {
			const created = await createOpenThread(selectedSnapshot.id, {
				title,
				description: newThreadDescriptionDraft.trim() || null,
				status: 'open',
			});
			openThreads = await listOpenThreads(selectedSnapshot.id);
			newThreadTitleDraft = '';
			newThreadDescriptionDraft = '';
			await selectOpenThread(created);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			creatingThread = false;
		}
	}

	async function toggleSelectedThreadStatus() {
		if (!selectedSnapshot || !selectedOpenThread) return;
		const nextStatus = selectedOpenThread.status === 'closed' ? 'open' : 'closed';

		error = null;
		try {
			const updated = await updateOpenThread(selectedSnapshot.id, selectedOpenThread.id, {
				status: nextStatus,
			});
			selectedOpenThread = updated;
			openThreads = await listOpenThreads(selectedSnapshot.id);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function addThreadRef() {
		if (!selectedSnapshot || !selectedOpenThread) return;
		const versionId = refArtifactVersionIdDraft.trim();
		if (!versionId) return;

		error = null;
		addingThreadRef = true;
		try {
			await createOpenThreadRef(selectedSnapshot.id, selectedOpenThread.id, {
				artifact_version_id: versionId,
				ref_kind: refKindDraft,
				quote: refQuoteDraft.trim() || null,
			});
			refQuoteDraft = '';
			openThreadRefs = await listOpenThreadRefs(selectedSnapshot.id, selectedOpenThread.id);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			addingThreadRef = false;
		}
	}

	function useCurrentVersionForRef() {
		if (!selectedArtifactVersion) return;
		refArtifactVersionIdDraft = selectedArtifactVersion.id;
	}

	function downloadTextFile(filename: string, text: string, contentType: string) {
		const blob = new Blob([text], { type: contentType || 'text/plain;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;
		a.click();
		URL.revokeObjectURL(url);
	}

	async function addGlossary() {
		if (!selectedSnapshot) return;
		const term = glossaryTermDraft.trim();
		const replacement = glossaryReplacementDraft.trim();
		if (!term || !replacement) return;

		error = null;
		creatingGlossaryEntry = true;
		try {
			await createGlossaryEntry(selectedSnapshot.id, { term, replacement });
			glossaryEntries = await listGlossaryEntries(selectedSnapshot.id);
			glossaryTermDraft = '';
			glossaryReplacementDraft = '';
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			creatingGlossaryEntry = false;
		}
	}

	async function downloadNovelMd() {
		if (!selectedSnapshot) return;
		error = null;
		exportingNovelMd = true;
		try {
			const resp = await exportNovelMarkdown(selectedSnapshot.id, {
				apply_glossary: applyGlossaryOnExport,
			});
			downloadTextFile(resp.filename, resp.text, resp.content_type);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			exportingNovelMd = false;
		}
	}

	async function downloadNovelTxt() {
		if (!selectedSnapshot) return;
		error = null;
		exportingNovelTxt = true;
		try {
			const resp = await exportNovelText(selectedSnapshot.id, {
				apply_glossary: applyGlossaryOnExport,
			});
			downloadTextFile(resp.filename, resp.text, resp.content_type);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			exportingNovelTxt = false;
		}
	}

	async function downloadScriptFountain() {
		if (!selectedSnapshot) return;
		error = null;
		exportingScriptFountain = true;
		try {
			const resp = await exportScriptFountain(selectedSnapshot.id, {
				apply_glossary: applyGlossaryOnExport,
			});
			downloadTextFile(resp.filename, resp.text, resp.content_type);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			exportingScriptFountain = false;
		}
	}

	async function openArtifactVersionFromIssue(versionId: string) {
		error = null;
		try {
			const v = await getArtifactVersion(versionId);
			let artifact = artifacts.find((a) => a.id === v.artifact_id) ?? null;
			if (!artifact) {
				artifacts = await listArtifacts();
				artifact = artifacts.find((a) => a.id === v.artifact_id) ?? null;
			}
			if (!artifact) {
				throw new Error(`artifact_not_found ${v.artifact_id}`);
			}
			await selectArtifact(artifact);
			selectArtifactVersion(v);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function selectSnapshot(snap: BriefSnapshotRead) {
		if (selectedSnapshot?.id !== snap.id) {
			closeRunEvents();
			autoRunning = false;
			selectedRun = null;
			workflowSteps = [];
			selectedStep = null;
		}
		selectedSnapshot = snap;
		showSnapshotJson = false;
		await refreshAnalysis();
	}

	async function createNewBrief() {
		error = null;
		creatingBrief = true;
		try {
			const brief = await createBrief({ title: newBriefTitle.trim() || null });
			newBriefTitle = '';
			await refreshAll();
			await selectBrief(brief);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			creatingBrief = false;
		}
	}

	async function createNewSnapshot() {
		if (!selectedBrief) return;
		error = null;
		creatingSnapshot = true;
		try {
			const snap = await createBriefSnapshot(selectedBrief.id, {
				label: newSnapshotLabel.trim() || null,
			});
			newSnapshotLabel = '';
			briefSnapshots = await listBriefSnapshots(selectedBrief.id);
			selectedSnapshot = snap;
			showSnapshotJson = false;
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			creatingSnapshot = false;
		}
	}

	async function deleteBriefFromUi(brief: BriefRead) {
		const title = brief.title ?? '（未命名）';
		if (!confirm(`确定删除 Brief「${title}」及其所有版本 / runs / 产物吗？此操作不可撤销。`)) return;

		error = null;
		try {
			await deleteBrief(brief.id);
			if (selectedBrief?.id === brief.id) {
				closeRunEvents();
				autoRunning = false;
				selectedBrief = null;
				selectedSnapshot = null;
				selectedRun = null;
				selectedStep = null;
				briefSnapshots = [];
				briefMessages = [];
				gapReport = null;
				workflowSteps = [];
				clearPropagation();
				knowledgeGraph = null;
				lintIssues = [];
				openThreads = [];
				selectedOpenThread = null;
				openThreadRefs = [];
				glossaryEntries = [];
			}
			selectedArtifact = null;
			artifactVersions = [];
			selectedArtifactVersion = null;
			artifactEditorDraft = '';
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function deleteSnapshotFromUi(snap: BriefSnapshotRead) {
		const label = snap.label ?? '（未命名）';
		if (!confirm(`确定删除版本「${label}」及其 runs / 产物吗？此操作不可撤销。`)) return;

		error = null;
		try {
			await deleteBriefSnapshot(snap.id);

			if (selectedSnapshot?.id === snap.id) {
				closeRunEvents();
				autoRunning = false;
				selectedSnapshot = null;
				selectedRun = null;
				selectedStep = null;
				workflowSteps = [];
				clearPropagation();
				knowledgeGraph = null;
				lintIssues = [];
				openThreads = [];
				selectedOpenThread = null;
				openThreadRefs = [];
				glossaryEntries = [];
			}
			if (selectedRun?.brief_snapshot_id === snap.id) {
				closeRunEvents();
				autoRunning = false;
				selectedRun = null;
				selectedStep = null;
				workflowSteps = [];
			}
			if (selectedArtifactVersion?.brief_snapshot_id === snap.id) {
				selectedArtifact = null;
				artifactVersions = [];
				selectedArtifactVersion = null;
				artifactEditorDraft = '';
				clearPropagation();
			}

			await refreshAll();
			if (selectedBrief?.id === snap.brief_id) {
				briefSnapshots = await listBriefSnapshots(selectedBrief.id);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function deleteRunFromUi(run: WorkflowRunRead) {
		if (!confirm(`确定删除该 workflow run 及其 step 记录/产物吗？此操作不可撤销。`)) return;

		error = null;
		try {
			await deleteWorkflowRun(run.id);
			if (selectedRun?.id === run.id) {
				closeRunEvents();
				autoRunning = false;
				selectedRun = null;
				selectedStep = null;
				workflowSteps = [];
			}
			if (selectedArtifactVersion?.workflow_run_id === run.id) {
				selectedArtifact = null;
				artifactVersions = [];
				selectedArtifactVersion = null;
				artifactEditorDraft = '';
				clearPropagation();
			}
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function saveGlobalPrefs() {
		error = null;
		savingGlobalPrefs = true;
		try {
			const maxFix = Number(globalMaxFixAttemptsDraft);
			globalOutputSpec = await patchGlobalOutputSpecDefaults({
				language: globalLanguageDraft.trim() || null,
				script_format: globalScriptFormatDraft,
				script_format_notes: globalScriptNotesDraft.trim() ? globalScriptNotesDraft.trim() : null,
				max_fix_attempts: Number.isFinite(maxFix) && maxFix >= 0 ? Math.floor(maxFix) : null,
			});
			syncGlobalDrafts();
			syncBriefOverrideDrafts();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			savingGlobalPrefs = false;
		}
	}

	async function saveBriefPrefs() {
		if (!selectedBrief) return;
		error = null;
		savingBriefPrefs = true;
		try {
			const maxFix = Number(briefMaxFixAttemptsDraft);
			const parsedMaxFix =
				Number.isFinite(maxFix) && maxFix >= 0 ? Math.floor(maxFix) : null;
			const updated = await patchBriefOutputSpecOverrides(selectedBrief.id, {
				language: overrideLanguage ? briefLanguageDraft.trim() || null : null,
				script_format: overrideScriptFormat ? briefScriptFormatDraft : null,
				script_format_notes: overrideScriptNotes ? briefScriptNotesDraft : null,
				max_fix_attempts: overrideMaxFixAttempts ? parsedMaxFix : null,
			});
			selectedBrief = updated;
			await refreshAll();
			syncBriefOverrideDrafts();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			savingBriefPrefs = false;
		}
	}

	async function resetBriefPrefsToGlobal() {
		if (!selectedBrief) return;
		overrideLanguage = false;
		overrideScriptFormat = false;
		overrideScriptNotes = false;
		overrideMaxFixAttempts = false;
		await saveBriefPrefs();
	}

	async function sendMessage() {
		if (!selectedBrief) return;
		const text = messageDraft.trim();
		if (!text) return;

		error = null;
		sendingMessage = true;
		const briefId = selectedBrief.id;
		const now = new Date().toISOString();
		const userTempId = tempId('temp-user');
		const assistantTempId = tempId('temp-assistant');
		briefMessages = [
			...briefMessages,
			{
				id: userTempId,
				brief_id: briefId,
				role: 'user',
				content_text: text,
				metadata: {},
				created_at: now,
			},
			{
				id: assistantTempId,
				brief_id: briefId,
				role: 'assistant',
				content_text: '…',
				metadata: { streaming: true },
				created_at: now,
			},
		];
		messageDraft = '';
		await tick();
		autosizeMessageTextarea();
		try {
			await streamBriefMessage(
				briefId,
				{ content_text: text, mode: selectedMode },
				{
					onAssistantDelta: (append) => {
						briefMessages = briefMessages.map((m) =>
							m.id === assistantTempId
								? {
										...m,
										content_text: m.content_text === '…' ? append : m.content_text + append,
									}
								: m,
						);
					},
					onFinal: (resp) => {
						selectedBrief = resp.brief;
						gapReport = resp.gap_report;
						briefMessages = resp.messages;
					},
					onError: (detail) => {
						error = detail;
					},
				},
			);
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			sendingMessage = false;
		}
	}

	async function createRun() {
		if (!selectedSnapshot) return;
		error = null;
		creatingRun = true;
		try {
			const run = await createWorkflowRun({
				kind: workflowKindDraft,
				brief_snapshot_id: selectedSnapshot.id,
			});
			await refreshAll();
			await selectRun(run);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			creatingRun = false;
		}
	}

	function resetRunStateDraft() {
		if (!selectedRun) return;
		runStateDraft = JSON.stringify(selectedRun.state, null, 2);
	}

	async function saveRunState() {
		if (!selectedRun) return;
		error = null;
		savingRunState = true;
		try {
			const parsed = JSON.parse(runStateDraft) as Record<string, unknown>;
			const updated = await patchWorkflowRun(selectedRun.id, { state: parsed });
			selectedRun = updated;
			runStateDraft = JSON.stringify(updated.state, null, 2);
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			savingRunState = false;
		}
	}

	async function forkSelectedRun() {
		if (!selectedRun) return;
		error = null;
		forkingRun = true;
		try {
			const forked = await forkWorkflowRun(selectedRun.id, { step_id: selectedStep?.id ?? null });
			await refreshAll();
			await selectRun(forked);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			forkingRun = false;
		}
	}

	async function sendIntervention() {
		if (!selectedRun) return;
		const instruction = interventionDraft.trim();
		if (!instruction) return;

		error = null;
		sendingIntervention = true;
		try {
			const resp: WorkflowInterventionResponse = await applyWorkflowIntervention(selectedRun.id, {
				instruction,
				step_id: selectedStep?.id ?? null,
			});
			selectedRun = resp.run;
			runStateDraft = JSON.stringify(resp.run.state, null, 2);
			workflowSteps = await listWorkflowSteps(resp.run.id);
			selectedStep = resp.step;
			interventionDraft = '';
			await tick();
			autosizeInterventionTextarea();
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			sendingIntervention = false;
		}
	}

	async function clearInterventionDraft() {
		interventionDraft = '';
		await tick();
		autosizeInterventionTextarea();
	}

	async function runNext() {
		if (!selectedRun) return;

		error = null;
		stepping = true;
		try {
			const resp = await executeWorkflowNext(selectedRun.id);
			selectedRun = resp.run;
			selectedStep = resp.step;
			workflowSteps = await listWorkflowSteps(resp.run.id);
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			stepping = false;
		}
	}

	function closeRunEvents() {
		if (runEvents) {
			runEvents.close();
			runEvents = null;
		}
	}

	function upsertRun(run: WorkflowRunRead) {
		if (selectedRun?.id === run.id) {
			selectedRun = run;
		}
		workflowRuns = workflowRuns.map((r) => (r.id === run.id ? run : r));
		if (!['queued', 'running'].includes(run.status)) {
			autoRunning = false;
		}
	}

	function upsertStep(step: WorkflowStepRunRead) {
		const idx = workflowSteps.findIndex((s) => s.id === step.id);
		if (idx >= 0) {
			workflowSteps = workflowSteps.map((s) => (s.id === step.id ? step : s));
		} else {
			workflowSteps = [...workflowSteps, step].sort((a, b) => {
				const ai = a.step_index ?? 0;
				const bi = b.step_index ?? 0;
				return ai - bi;
			});
		}
		if (step.status === 'running' && selectedRun?.id === step.workflow_run_id) {
			selectedStep = step;
			if (!(step.id in llmStreamByStep)) {
				llmStreamByStep = { ...llmStreamByStep, [step.id]: '' };
			}
		}
		if (selectedStep?.id === step.id) {
			selectedStep = step;
		}
	}

	function subscribeToRunEvents(runId: string) {
		closeRunEvents();
		const url = workflowRunEventsUrl(runId);
		const es = new EventSource(url);
		runEvents = es;

		es.addEventListener('run', (evt) => {
			try {
				const payload = JSON.parse((evt as MessageEvent).data) as { run: WorkflowRunRead };
				upsertRun(payload.run);
			} catch (e) {
				// ignore
			}
		});

		es.addEventListener('step', (evt) => {
			try {
				const payload = JSON.parse((evt as MessageEvent).data) as { step: WorkflowStepRunRead };
				upsertStep(payload.step);
			} catch (e) {
				// ignore
			}
		});

		es.addEventListener('llm_start', (evt) => {
			try {
				const payload = JSON.parse((evt as MessageEvent).data) as {
					step_id: string;
					step_name?: string;
				};
				if (!payload.step_id) return;
				llmStreamByStep = { ...llmStreamByStep, [payload.step_id]: '' };
			} catch (e) {
				// ignore
			}
		});

		es.addEventListener('llm_delta', (evt) => {
			try {
				const payload = JSON.parse((evt as MessageEvent).data) as { step_id: string; append: string };
				if (!payload.step_id) return;
				const existing = llmStreamByStep[payload.step_id] ?? '';
				llmStreamByStep = { ...llmStreamByStep, [payload.step_id]: existing + (payload.append ?? '') };
			} catch (e) {
				// ignore
			}
		});

		es.addEventListener('llm_end', (evt) => {
			try {
				const payload = JSON.parse((evt as MessageEvent).data) as { step_id: string };
				if (!payload.step_id) return;
				if (!(payload.step_id in llmStreamByStep)) {
					llmStreamByStep = { ...llmStreamByStep, [payload.step_id]: '' };
				}
			} catch (e) {
				// ignore
			}
		});

		es.addEventListener('log', (evt) => {
			try {
				const payload = JSON.parse((evt as MessageEvent).data) as { message: string };
				if (payload.message === 'autorun_stopped') {
					autoRunning = false;
				}
			} catch (e) {
				// ignore
			}
		});

		es.onerror = () => {
			// Keep UI usable even if stream drops; user can refresh/reselect the run.
		};
	}

	async function pauseRun() {
		if (!selectedRun) return;
		error = null;
		try {
			const resp = await pauseWorkflowRun(selectedRun.id);
			selectedRun = resp.run;
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function resumeRun() {
		if (!selectedRun) return;
		error = null;
		try {
			const resp = await resumeWorkflowRun(selectedRun.id);
			selectedRun = resp.run;
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function stopAuto() {
		if (!selectedRun) return;
		error = null;
		try {
			await stopWorkflowAutorun(selectedRun.id);
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			autoRunning = false;
		}
	}

	async function startAuto() {
		if (!selectedRun) return;
		error = null;
		autoRunning = true;
		try {
			const resp = await startWorkflowAutorun(selectedRun.id);
			selectedRun = resp.run;
			await refreshAll();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
			autoRunning = false;
		}
	}

	function cursorSummary(run: WorkflowRunRead | null): string {
		if (!run) return '';
		const cursor = (run.state as any)?.cursor as any;
		if (!cursor || typeof cursor !== 'object') return '';
		const phase = cursor.phase ? String(cursor.phase) : '';
		const chapter = cursor.chapter_index ? `章${cursor.chapter_index}` : '';
		const scene = cursor.scene_index ? `场${cursor.scene_index}` : '';
		const parts = [phase, chapter || scene].filter(Boolean);
		return parts.join(' · ');
	}

	function runDisplayName(run: WorkflowRunRead): string {
		const kindLabel =
			run.kind === 'novel' ? '小说' : run.kind === 'script' ? '剧本' : run.kind === 'novel_to_script' ? '小说→剧本' : run.kind;

		const cursor = (run.state as any)?.cursor as any;
		const phase = cursor && typeof cursor === 'object' ? String(cursor.phase ?? '') : '';
		const chapterIndex = cursor && typeof cursor === 'object' ? Number(cursor.chapter_index ?? 0) : 0;
		const sceneIndex = cursor && typeof cursor === 'object' ? Number(cursor.scene_index ?? 0) : 0;

		if (!phase) return `${kindLabel} · 未开始`;

		if (run.kind === 'novel') {
			if (phase === 'novel_outline') return `${kindLabel} · 大纲`;
			if (phase === 'novel_beats') return `${kindLabel} · 分章`;
			if (phase === 'novel_chapter_draft') return `${kindLabel} · 第${chapterIndex || 1}章 · 草稿`;
			if (phase === 'novel_chapter_critic') return `${kindLabel} · 第${chapterIndex || 1}章 · 审校`;
			if (phase === 'novel_chapter_fix') return `${kindLabel} · 第${chapterIndex || 1}章 · 修复`;
			if (phase === 'novel_chapter_commit') return `${kindLabel} · 第${chapterIndex || 1}章 · 提交`;
			if (phase === 'done') return `${kindLabel} · 完成`;
			return `${kindLabel} · ${phase}`;
		}

		if (run.kind === 'script') {
			if (phase === 'script_scene_list') return `${kindLabel} · 场景列表`;
			if (phase === 'script_scene_draft') return `${kindLabel} · 第${sceneIndex || 1}场 · 草稿`;
			if (phase === 'script_scene_critic') return `${kindLabel} · 第${sceneIndex || 1}场 · 审校`;
			if (phase === 'script_scene_fix') return `${kindLabel} · 第${sceneIndex || 1}场 · 修复`;
			if (phase === 'script_scene_commit') return `${kindLabel} · 第${sceneIndex || 1}场 · 提交`;
			if (phase === 'done') return `${kindLabel} · 完成`;
			return `${kindLabel} · ${phase}`;
		}

		if (run.kind === 'novel_to_script') {
			if (phase === 'nts_scene_list') return `${kindLabel} · 场景列表`;
			if (phase === 'nts_scene_draft') return `${kindLabel} · 第${sceneIndex || 1}场 · 草稿`;
			if (phase === 'nts_scene_critic') return `${kindLabel} · 第${sceneIndex || 1}场 · 审校`;
			if (phase === 'nts_scene_fix') return `${kindLabel} · 第${sceneIndex || 1}场 · 修复`;
			if (phase === 'nts_scene_commit') return `${kindLabel} · 第${sceneIndex || 1}场 · 提交`;
			if (phase === 'done') return `${kindLabel} · 完成`;
			return `${kindLabel} · ${phase}`;
		}

		return `${kindLabel} · ${phase}`;
	}

	function translateWorkflowErrorDetail(detail: string): string {
		const mapping: Record<string, string> = {
			hard_check_failed: '硬一致性检查失败',
			max_fix_attempts_exceeded: '修复次数超过上限',
			novel_source_missing: '缺少小说来源（无法转写）',
			step_failed: '步骤执行失败',
		};
		return mapping[detail] ?? detail;
	}

	function runErrorSummary(err: Record<string, unknown> | null): string {
		if (!err) return '';
		const detail = typeof (err as any).detail === 'string' ? ((err as any).detail as string) : '';
		const detailLabel = detail ? translateWorkflowErrorDetail(detail) : '';
		const hardErrors = Array.isArray((err as any).hard_errors) ? ((err as any).hard_errors as unknown[]) : null;
		const hardText = hardErrors && hardErrors.length ? hardErrors.map(String).join(', ') : '';
		const errorType = typeof (err as any).error_type === 'string' ? ((err as any).error_type as string) : '';
		const message = typeof (err as any).error === 'string' ? ((err as any).error as string) : '';

		const parts = [detailLabel || detail, errorType ? `(${errorType})` : '', hardText || message].filter(Boolean);
		return parts.join(' ');
	}

	$: {
		const snapshotId = selectedSnapshot?.id;
		visibleWorkflowRuns = snapshotId
			? workflowRuns.filter((r) => r.brief_snapshot_id === snapshotId)
			: [];
	}

	$: {
		interventionSteps = workflowSteps
			.filter((step) => step.step_name === 'intervention')
			.slice()
			.sort((a, b) => (b.step_index ?? 0) - (a.step_index ?? 0));
	}

	$: {
		lastFailedStep =
			workflowSteps
				.filter((step) => step.status === 'failed')
				.slice()
				.sort((a, b) => (b.step_index ?? 0) - (a.step_index ?? 0))[0] ?? null;
	}

	onMount(async () => {
		await refreshAll();
		await refreshSettings();
		await refreshProviderSettings();
	});

	onDestroy(() => {
		closeRunEvents();
	});
</script>

<div class="h-screen overflow-hidden bg-zinc-950 text-zinc-100">
	<div class="flex h-full min-h-0 flex-col">
		<header class="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
			<div class="text-sm font-semibold">writer_agent2 · IDE (foundation)</div>
			<div class="flex items-center gap-2">
				<button
					class="rounded-md bg-zinc-800 px-3 py-1.5 text-xs hover:bg-zinc-700"
					onclick={refreshAll}
				>
					刷新
				</button>
			</div>
		</header>

		{#if error}
			<div class="border-b border-red-900/50 bg-red-950/50 px-4 py-2 text-xs text-red-200">
				{error}
			</div>
		{/if}

		<div class="grid min-h-0 flex-1 grid-cols-[320px_1fr_360px]">
			<!-- Left: Chat -->
			<section class="flex min-h-0 flex-col border-r border-zinc-800">
				<div class="border-b border-zinc-800 px-4 py-3 text-xs font-semibold text-zinc-300">
					对话
				</div>
				<div class="min-h-0 flex-1 space-y-3 overflow-auto p-4 text-sm text-zinc-300">
					{#if selectedBrief}
						{#each briefMessages as m (m.id)}
							<div class="rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2">
								<div class="mb-1 text-[10px] font-semibold text-zinc-500">
									{m.role} · {new Date(m.created_at).toLocaleString()}
								</div>
								<div class="whitespace-pre-wrap text-xs text-zinc-200">{m.content_text}</div>
							</div>
						{/each}
						{#if briefMessages.length === 0}
							<p class="text-xs text-zinc-500">暂无对话记录。</p>
						{/if}
					{:else}
						<p class="text-zinc-400">先在右侧选择一个 Brief，然后在这里对话补全创作简报。</p>
					{/if}
				</div>
				<div class="border-t border-zinc-800 p-3">
					<div class="flex items-end gap-2">
						<select
							class="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-2 text-xs text-zinc-200"
							bind:value={selectedMode}
							disabled={!selectedBrief || sendingMessage}
						>
							<option value="novel">小说</option>
							<option value="script">剧本</option>
							<option value="novel_to_script">小说→剧本</option>
						</select>
						<textarea
							class="max-h-40 flex-1 resize-none overflow-y-auto rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm leading-5 outline-none placeholder:text-zinc-600"
							placeholder={selectedBrief ? '输入想法…' : '请选择一个 Brief…'}
							rows="1"
							bind:this={messageTextarea}
							bind:value={messageDraft}
							disabled={!selectedBrief || sendingMessage}
							oninput={autosizeMessageTextarea}
							onkeydown={(e) => {
								if (e.key === 'Enter' && !e.shiftKey) {
									e.preventDefault();
									sendMessage();
								}
							}}
						></textarea>
						<button
							class="rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
							onclick={sendMessage}
							disabled={!selectedBrief || sendingMessage || messageDraft.trim().length === 0}
						>
							发送
						</button>
					</div>
				</div>
			</section>

			<!-- Middle: Workflow -->
			<section class="flex min-h-0 flex-col border-r border-zinc-800">
				<div class="border-b border-zinc-800 px-4 py-3 text-xs font-semibold text-zinc-300">
					工作流
				</div>
				<div class="min-h-0 flex-1 overflow-auto p-4">
					{#if selectedArtifact}
						<div class="rounded-md border border-zinc-800 bg-zinc-900 p-3">
							<div class="mb-2 flex items-center justify-between gap-2">
								<div class="truncate text-xs font-semibold text-zinc-300">
									Artifact 编辑 · {selectedArtifact.title ?? selectedArtifact.kind}
								</div>
								<div class="text-[11px] text-zinc-500">{selectedArtifact.ordinal ?? ''}</div>
							</div>

							{#if selectedArtifactVersion}
								<div class="mb-3 flex flex-wrap items-center gap-2 text-[11px] text-zinc-400">
									<div class="rounded bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-200">
										{selectedArtifactVersion.source}
									</div>
									<div>{new Date(selectedArtifactVersion.created_at).toLocaleString()}</div>
									{#if selectedArtifactVersion.brief_snapshot_id}
										<div class="truncate">
											snapshot: {selectedArtifactVersion.brief_snapshot_id}
										</div>
									{:else}
										<div class="truncate text-zinc-500">snapshot: (none)</div>
									{/if}
								</div>

								<textarea
									class="h-[420px] w-full resize-none rounded-md border border-zinc-800 bg-zinc-950/30 p-3 text-xs text-zinc-200 outline-none"
									bind:this={artifactTextarea}
									bind:value={artifactEditorDraft}
									disabled={savingArtifactVersion}
								></textarea>

								<div class="mt-3 flex gap-2">
									<button
										class="flex-1 rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
										onclick={saveArtifactEdit}
										disabled={savingArtifactVersion || artifactEditorDraft.trim().length === 0}
									>
										保存为新版本（user）
									</button>
									<button
										class="rounded-md bg-zinc-800 px-3 py-2 text-xs hover:bg-zinc-700 disabled:opacity-50"
										onclick={resetArtifactDraft}
										disabled={savingArtifactVersion}
									>
										重置
									</button>
								</div>

								<div class="mt-2 text-[10px] text-zinc-500">
									保存不会覆盖旧版本，会创建新版本；并继承 base 版本的 `brief_snapshot_id`（用于
									RAG）。
								</div>

								<div class="mt-4 rounded-md border border-zinc-800 bg-zinc-950/30 p-3 text-xs">
									<div class="mb-2 flex items-center justify-between gap-2">
										<div class="font-semibold text-zinc-200">定向重写（创建新版本）</div>
										<button
											class="rounded-md bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700 disabled:opacity-50"
											onclick={captureRewriteSelection}
											disabled={!artifactTextarea || rewritingSelection}
										>
											读取选区
										</button>
									</div>

									<div class="mb-2 text-[11px] text-zinc-500">
										{#if rewriteSelectionStart !== null && rewriteSelectionEnd !== null}
											选区：{rewriteSelectionStart} - {rewriteSelectionEnd}
										{:else}
											选区：未选择
										{/if}
									</div>

									<input
										class="mb-2 w-full rounded-md border border-zinc-800 bg-zinc-900 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 disabled:opacity-60"
										placeholder="指令（例如：把旧城改成新城，并保持语气冷峻）"
										bind:value={rewriteInstructionDraft}
										disabled={rewritingSelection}
									/>
									<button
										class="w-full rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
										onclick={runTargetedRewrite}
										disabled={rewritingSelection ||
											rewriteInstructionDraft.trim().length === 0 ||
											rewriteSelectionStart === null ||
											rewriteSelectionEnd === null ||
											rewriteSelectionStart === rewriteSelectionEnd}
									>
										{rewritingSelection ? '重写中…' : '定向重写'}
									</button>
								</div>

								{#if previewingPropagation}
									<div class="mt-4 rounded-md border border-zinc-800 bg-zinc-950/30 p-3 text-xs">
										<div class="font-semibold text-zinc-200">改动传播预览生成中…</div>
									</div>
								{:else if propagationPreview}
									<div class="mt-4 rounded-md border border-zinc-800 bg-zinc-950/30 p-3 text-xs">
										<div class="mb-2 flex items-center justify-between gap-2">
											<div class="font-semibold text-zinc-200">改动传播预览</div>
											<div class="text-[11px] text-zinc-500">
												impacts: {propagationPreview.impacts.length}
											</div>
										</div>

										<div class="whitespace-pre-wrap text-[11px] text-zinc-300">
											{propagationPreview.fact_changes}
										</div>

										{#if propagationPreview.impacts.length > 0}
											<div class="mt-3 space-y-1">
												{#each propagationPreview.impacts as imp (imp.artifact_id)}
													<div class="rounded border border-zinc-800 bg-zinc-900/60 p-2">
														<div class="flex items-center justify-between gap-2">
															<div class="truncate text-[11px] text-zinc-200">
																{imp.kind} · {imp.ordinal ?? ''} · {imp.title ?? imp.artifact_id}
															</div>
														</div>
														<div class="mt-1 text-[11px] text-zinc-400">{imp.reason}</div>
													</div>
												{/each}
											</div>

											<div class="mt-3">
												<button
													class="w-full rounded-md bg-amber-700 px-3 py-2 text-xs font-semibold hover:bg-amber-600 disabled:opacity-50"
													onclick={applyAndRepairPropagation}
													disabled={repairingPropagation}
												>
													{repairingPropagation ? '修复中…' : '一键修复下游（创建新版本）'}
												</button>
												{#if propagationEvent}
													<div class="mt-2 text-[10px] text-zinc-500">
														event: {propagationEvent.id}
													</div>
												{/if}
												{#if propagationImpacts.length > 0}
													<div class="mt-2 text-[10px] text-zinc-500">
														已标记并修复：{propagationImpacts.length}
													</div>
												{/if}
											</div>
										{:else}
											<div class="mt-3 text-[11px] text-zinc-500">未检测到需要修复的下游产物。</div>
										{/if}
									</div>
								{/if}
							{:else}
								<div class="text-xs text-zinc-500">请在右侧选择一个版本开始编辑。</div>
							{/if}
						</div>
					{:else}
						{#if selectedBrief}
							<div class="mb-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
								<div class="mb-2 text-xs font-semibold text-zinc-300">从 Snapshot 创建 Run</div>
								<div class="flex flex-wrap items-center gap-2">
									<div class="text-[11px] text-zinc-400">
										{#if selectedSnapshot}
											已选：{selectedSnapshot.label ?? '（未命名）'} ·
											{new Date(selectedSnapshot.created_at).toLocaleString()}
										{:else}
											请先在右侧 Snapshots 里选择一个
										{/if}
									</div>
									<div class="flex-1"></div>
									<select
										class="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-200"
										bind:value={workflowKindDraft}
										disabled={creatingRun}
									>
										<option value="novel">小说</option>
										<option value="script">剧本</option>
										<option value="novel_to_script">小说→剧本</option>
									</select>
									<button
										class="rounded-md bg-emerald-700 px-3 py-1.5 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
										onclick={createRun}
										disabled={!selectedSnapshot || creatingRun}
									>
										创建
									</button>
								</div>
							</div>
						{/if}

						<div class="mb-3 text-xs font-semibold text-zinc-400">Workflow Runs</div>
						{#if selectedSnapshot}
							<div class="space-y-1">
								{#each visibleWorkflowRuns as run (run.id)}
									<div class="flex gap-2">
										<button
											class="flex flex-1 items-start justify-between rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-left text-xs hover:bg-zinc-800"
											class:border-emerald-700={selectedRun?.id === run.id}
											onclick={() => selectRun(run)}
										>
											<div class="min-w-0 flex-1">
												<div class="flex items-center justify-between gap-2">
													<span class="truncate">{runDisplayName(run)}</span>
													<span
														class="ml-2 rounded bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-200"
														>{run.status}</span
													>
												</div>
												{#if run.status === 'failed'}
													<div class="mt-1 truncate text-[10px] text-red-200/80">
														{runErrorSummary(run.error) || '（无错误详情）'}
													</div>
												{/if}
											</div>
										</button>
										<button
											class="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-xs text-red-200 hover:bg-red-950/60"
											onclick={() => deleteRunFromUi(run)}
										>
											删除
										</button>
									</div>
								{/each}
								{#if visibleWorkflowRuns.length === 0}
									<div class="text-xs text-zinc-500">该版本暂无 runs</div>
								{/if}
							</div>
						{:else}
							<div class="text-xs text-zinc-500">请先在右侧选择一个 Snapshot 才能查看 runs。</div>
						{/if}

						{#if selectedRun}
							<div class="mt-6">
								<div class="mb-2 flex items-center justify-between gap-2">
									<div class="text-xs font-semibold text-zinc-400">
										Steps · {runDisplayName(selectedRun)} · {selectedRun.status}
									</div>
									<div class="text-[11px] text-zinc-500">{cursorSummary(selectedRun)}</div>
								</div>

								<div class="mb-3 flex flex-wrap items-center gap-2">
									<button
										class="rounded-md bg-zinc-800 px-3 py-1.5 text-xs hover:bg-zinc-700 disabled:opacity-50"
										onclick={forkSelectedRun}
										disabled={forkingRun}
									>
										{forkingRun ? 'Forking…' : 'Fork'}
									</button>
									<button
										class="rounded-md bg-zinc-800 px-3 py-1.5 text-xs hover:bg-zinc-700 disabled:opacity-50"
										onclick={runNext}
										disabled={stepping ||
											autoRunning ||
											!['queued', 'running', 'failed'].includes(selectedRun.status)}
									>
										{selectedRun.status === 'failed' ? '重试' : '下一步'}
									</button>
									<button
										class="rounded-md bg-zinc-800 px-3 py-1.5 text-xs hover:bg-zinc-700 disabled:opacity-50"
										onclick={pauseRun}
										disabled={stepping || !['queued', 'running'].includes(selectedRun.status)}
									>
										暂停
									</button>
									<button
										class="rounded-md bg-zinc-800 px-3 py-1.5 text-xs hover:bg-zinc-700 disabled:opacity-50"
										onclick={resumeRun}
										disabled={stepping || selectedRun.status !== 'paused'}
									>
										继续
									</button>
									{#if autoRunning}
										<button
											class="rounded-md bg-amber-700 px-3 py-1.5 text-xs font-semibold hover:bg-amber-600"
											onclick={stopAuto}
										>
											停止自动
										</button>
									{:else}
										<button
											class="rounded-md bg-emerald-700 px-3 py-1.5 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
											onclick={startAuto}
											disabled={stepping || !['queued', 'running', 'failed'].includes(selectedRun.status)}
										>
											{selectedRun.status === 'failed' ? '重试自动' : '自动'}
										</button>
									{/if}
								</div>

								{#if selectedRun.status === 'failed'}
									<div class="mb-3 rounded-md border border-red-900/60 bg-red-950/30 p-3">
										<div class="mb-2 flex items-center justify-between gap-2">
											<div class="text-xs font-semibold text-red-200">运行失败</div>
											<div class="text-[11px] text-red-200/70">
												{runErrorSummary(selectedRun.error)}
											</div>
										</div>

										{#if selectedRun.error}
											<pre
												class="max-h-44 overflow-auto whitespace-pre-wrap rounded border border-red-900/40 bg-red-950/20 p-2 font-mono text-[11px] text-red-100">{JSON.stringify(
													selectedRun.error,
													null,
													2,
												)}</pre>
										{:else}
											<div class="text-[11px] text-red-200/70">（无 error payload）</div>
										{/if}

										{#if lastFailedStep}
											<div class="mt-2 text-[11px] text-red-200/80">
												最近失败 step：{lastFailedStep.step_index ?? ''} · {lastFailedStep.step_name}
											</div>
											{#if lastFailedStep.error}
												<pre
													class="mt-1 max-h-32 overflow-auto whitespace-pre-wrap rounded border border-red-900/40 bg-red-950/20 p-2 font-mono text-[11px] text-red-100">{lastFailedStep.error}</pre>
											{/if}
										{/if}

										<div class="mt-2 text-[10px] text-red-200/70">
											提示：可点选失败 step 查看 outputs / error；也可用「节点对话干预」修正
											run.state 后点「重试」。
										</div>
									</div>
								{/if}

								<div class="mb-3 rounded-md border border-zinc-800 bg-zinc-900 p-3">
									<div class="mb-2 flex items-center justify-between gap-2">
										<div class="text-xs font-semibold text-zinc-300">Run State（可编辑）</div>
										<div class="flex gap-2">
											<button
												class="rounded-md bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700 disabled:opacity-50"
												onclick={resetRunStateDraft}
												disabled={savingRunState}
											>
												重置
											</button>
											<button
												class="rounded-md bg-emerald-700 px-2 py-1 text-[10px] font-semibold hover:bg-emerald-600 disabled:opacity-50"
												onclick={saveRunState}
												disabled={savingRunState}
											>
												{savingRunState ? '保存中…' : '保存'}
											</button>
										</div>
									</div>
									<textarea
										class="h-40 w-full resize-none rounded-md border border-zinc-800 bg-zinc-950/30 p-2 font-mono text-[11px] text-zinc-200 outline-none"
										bind:value={runStateDraft}
										disabled={savingRunState}
									></textarea>
									<div class="mt-2 text-[10px] text-zinc-500">
										提示：这里只是最小 MVP（直接 PATCH run.state）。编辑错误 JSON 会导致保存失败。
									</div>
								</div>

								<div class="mb-3 rounded-md border border-zinc-800 bg-zinc-900 p-3">
									<div class="mb-2 flex items-center justify-between gap-2">
										<div class="text-xs font-semibold text-zinc-300">节点对话干预（MVP）</div>
										<div class="text-[11px] text-zinc-500">
											目标：
											{#if selectedStep}
												{selectedStep.step_index ?? ''} · {selectedStep.step_name}
											{:else}
												Run
											{/if}
										</div>
									</div>

									<div class="mb-2 text-[10px] text-zinc-500">
										提示：先点选一个 step，再输入“怎么改”（例如：把主角名字改为… / 调整章节数为…）。
										系统会生成 `state_patch` 并合并到 run.state，然后追加一个 `intervention` step。
									</div>

									{#if interventionSteps.length > 0}
										<div class="mb-2 max-h-56 overflow-auto rounded-md border border-zinc-800 bg-zinc-950/30 p-2 text-[11px]">
											{#each interventionSteps as step (step.id)}
												<div class="mb-2 rounded border border-zinc-800 bg-zinc-950/40 p-2">
													<div class="mb-1 flex items-center justify-between gap-2">
														<div class="truncate font-semibold text-zinc-300">
															{step.step_index ?? ''} · 干预
														</div>
														<div class="text-[10px] text-zinc-500">
															{new Date(step.created_at).toLocaleString()}
														</div>
													</div>
													<div class="mb-1 text-[10px] text-zinc-500">
														目标：
														{((step.outputs as any)?.target_step_name as string) ?? 'run'}
													</div>
													<div class="mb-2">
														<div class="mb-0.5 text-[10px] text-zinc-500">指令</div>
														<div class="whitespace-pre-wrap text-zinc-200">
															{((step.outputs as any)?.instruction as string) ?? ''}
														</div>
													</div>
													<div>
														<div class="mb-0.5 text-[10px] text-zinc-500">AI</div>
														<div class="whitespace-pre-wrap text-zinc-200">
															{((step.outputs as any)?.assistant_message as string) ?? ''}
														</div>
													</div>
												</div>
											{/each}
										</div>
									{/if}

									<textarea
										class="max-h-40 w-full resize-none overflow-y-auto rounded-md border border-zinc-800 bg-zinc-950/30 px-3 py-2 text-sm leading-5 outline-none placeholder:text-zinc-600"
										placeholder={selectedRun ? '输入干预指令…' : '请选择 Run…'}
										rows="1"
										bind:this={interventionTextarea}
										bind:value={interventionDraft}
										disabled={!selectedRun || sendingIntervention}
										oninput={autosizeInterventionTextarea}
										onkeydown={(e) => {
											if (e.key === 'Enter' && !e.shiftKey) {
												e.preventDefault();
												sendIntervention();
											}
										}}
									></textarea>

									<div class="mt-2 flex gap-2">
										<button
											class="flex-1 rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
											onclick={sendIntervention}
											disabled={!selectedRun || sendingIntervention || interventionDraft.trim().length === 0}
										>
											{sendingIntervention ? '发送中…' : '发送干预'}
										</button>
										<button
											class="rounded-md bg-zinc-800 px-3 py-2 text-xs hover:bg-zinc-700 disabled:opacity-50"
											onclick={clearInterventionDraft}
											disabled={sendingIntervention || interventionDraft.length === 0}
										>
											清空
										</button>
									</div>
								</div>

								<div class="space-y-1">
									{#each workflowSteps as step (step.id)}
										<button
											class="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-left text-xs hover:bg-zinc-800"
											class:border-emerald-700={selectedStep?.id === step.id}
											onclick={() => (selectedStep = step)}
										>
											<div class="flex items-center justify-between">
												<div class="truncate">{step.step_index ?? ''} · {step.step_name}</div>
												<div class="text-[10px] text-zinc-400">{step.status}</div>
											</div>
										</button>
									{/each}
									{#if workflowSteps.length === 0}
										<div class="text-xs text-zinc-500">暂无 steps</div>
									{/if}
								</div>

								{#if selectedStep}
									<div class="mt-4 rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2">
										<div class="mb-2 text-xs font-semibold text-zinc-300">
											Step 输出 · {selectedStep.step_name}
										</div>
										{#if selectedStep.status === 'running' ||
										((llmStreamByStep[selectedStep.id] ?? '').length > 0)}
											<div class="mb-2 rounded border border-zinc-800 bg-zinc-950/30 p-2">
												<div class="mb-1 text-[10px] font-semibold text-zinc-300">
													实时输出（流式）
												</div>
												<pre
													class="max-h-52 overflow-auto whitespace-pre-wrap font-mono text-[11px] text-zinc-200">{llmStreamByStep[
														selectedStep.id
													] || '等待模型输出…'}</pre>
											</div>
										{/if}
										{#if (selectedStep.outputs as any)?.fact_digest || (selectedStep.outputs as any)?.tone_digest}
											<div class="mb-2 grid grid-cols-2 gap-2 text-[11px]">
												<div class="rounded border border-zinc-800 bg-zinc-950/30 p-2">
													<div class="mb-1 font-semibold text-zinc-400">Fact Digest</div>
													<div class="whitespace-pre-wrap text-zinc-200">
														{((selectedStep.outputs as any).fact_digest as string) ?? ''}
													</div>
												</div>
												<div class="rounded border border-zinc-800 bg-zinc-950/30 p-2">
													<div class="mb-1 font-semibold text-zinc-400">Tone Digest</div>
													<div class="whitespace-pre-wrap text-zinc-200">
														{((selectedStep.outputs as any).tone_digest as string) ?? ''}
													</div>
												</div>
											</div>
										{/if}
										<pre
											class="max-h-72 overflow-auto whitespace-pre-wrap text-[11px] text-zinc-300">{JSON.stringify(
												selectedStep.outputs,
												null,
												2,
											)}</pre>
										{#if selectedStep.error}
											<div class="mt-2 rounded border border-red-900/60 bg-red-950/30 p-2">
												<div class="mb-1 text-[10px] font-semibold text-red-200">error</div>
												<pre
													class="max-h-40 overflow-auto whitespace-pre-wrap font-mono text-[11px] text-red-100">{selectedStep.error}</pre>
											</div>
										{/if}
									</div>
								{/if}
							</div>
						{/if}
					{/if}
				</div>
			</section>

			<!-- Right: Assets -->
			<section class="flex min-h-0 flex-col">
				<div class="border-b border-zinc-800 px-4 py-3 text-xs font-semibold text-zinc-300">
					故事资产
				</div>
				<div class="min-h-0 flex-1 overflow-auto p-4">
					<div class="mb-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
						<div class="mb-2 flex items-center justify-between text-xs font-semibold text-zinc-300">
							<span>模型提供商（OpenAI 兼容）</span>
							<button
								class="rounded bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700"
								onclick={refreshProviderSettings}
							>
								刷新
							</button>
						</div>

						{#if llmProviderSettings}
							<div class="mb-2 text-[10px] text-zinc-500">
								API Key：{llmProviderSettings.api_key_configured ? '已配置' : '未配置'}（不回显）
							</div>

							<div class="space-y-2 text-xs">
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">Base URL</div>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										placeholder="https://api.openai.com/v1"
										bind:value={providerBaseUrlDraft}
										disabled={savingProviderSettings}
									/>
								</label>
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">Chat Model</div>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										placeholder="gpt-4o-mini"
										bind:value={providerModelDraft}
										disabled={savingProviderSettings}
									/>
								</label>
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">Embeddings Model</div>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										placeholder="text-embedding-3-small"
										bind:value={providerEmbeddingsModelDraft}
										disabled={savingProviderSettings}
									/>
								</label>
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">Timeout（秒）</div>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										type="number"
										min="1"
										step="1"
										bind:value={providerTimeoutDraft}
										disabled={savingProviderSettings}
									/>
								</label>
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">Max Retries（连接重试次数）</div>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										type="number"
										min="0"
										step="1"
										bind:value={providerMaxRetriesDraft}
										disabled={savingProviderSettings}
									/>
								</label>
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">API Key（不回显）</div>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										type="password"
										placeholder={llmProviderSettings.api_key_configured
											? '填入新 key 以更新（留空不变）'
											: '填入 key 以启用'}
										bind:value={providerApiKeyDraft}
										disabled={savingProviderSettings}
									/>
								</label>

								<div class="flex gap-2">
									<button
										class="flex-1 rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
										onclick={saveProviderSettings}
										disabled={savingProviderSettings}
									>
										保存配置
									</button>
									<button
										class="rounded-md bg-zinc-800 px-3 py-2 text-xs hover:bg-zinc-700 disabled:opacity-50"
										onclick={clearProviderApiKey}
										disabled={savingProviderSettings || !llmProviderSettings.api_key_configured}
									>
										清除 Key
									</button>
								</div>

								<div class="text-[10px] text-zinc-500">
									提示：只保存到服务端（单用户本地 DB），GET 不返回 key；留空 key 表示不修改。
								</div>
							</div>
						{:else}
							<div class="text-xs text-zinc-500">未加载（请检查 API 是否可用）</div>
						{/if}
					</div>

					<div class="mb-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
						<div class="mb-2 flex items-center justify-between text-xs font-semibold text-zinc-300">
							<span>全局偏好</span>
							<button
								class="rounded bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700"
								onclick={refreshSettings}
							>
								刷新
							</button>
						</div>

						{#if globalOutputSpec}
							<div class="space-y-2 text-xs">
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">语言（default）</div>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										placeholder="zh-CN"
										bind:value={globalLanguageDraft}
										disabled={savingGlobalPrefs}
									/>
								</label>
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">剧本格式（default）</div>
									<select
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200"
										bind:value={globalScriptFormatDraft}
										disabled={savingGlobalPrefs}
									>
										<option value="screenplay_int_ext">影视剧本（INT/EXT）</option>
										<option value="stage_play">舞台剧</option>
										<option value="custom">自定义</option>
									</select>
								</label>
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">格式备注（default）</div>
									<textarea
										class="w-full resize-none rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										rows="3"
										placeholder="例如：对白密度、镜头语言、场景标题格式…"
										bind:value={globalScriptNotesDraft}
										disabled={savingGlobalPrefs}
									></textarea>
								</label>
								<label class="block">
									<div class="mb-1 text-[10px] text-zinc-500">自动修复最大次数（default）</div>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none"
										type="number"
										min="0"
										step="1"
										bind:value={globalMaxFixAttemptsDraft}
										disabled={savingGlobalPrefs}
									/>
								</label>
								<button
									class="w-full rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
									onclick={saveGlobalPrefs}
									disabled={savingGlobalPrefs}
								>
									保存全局偏好
								</button>
							</div>
						{:else}
							<div class="text-xs text-zinc-500">未加载（请检查 API 是否可用）</div>
						{/if}
					</div>

					<div class="mb-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
						<div class="mb-2 text-xs font-semibold text-zinc-300">新建 Brief</div>
						<div class="flex gap-2">
							<input
								class="flex-1 rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600"
								placeholder="标题（可空）"
								bind:value={newBriefTitle}
								disabled={creatingBrief}
								onkeydown={(e) => e.key === 'Enter' && createNewBrief()}
							/>
							<button
								class="rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
								onclick={createNewBrief}
								disabled={creatingBrief}
							>
								创建
							</button>
						</div>
					</div>

					<div class="mb-3 text-xs font-semibold text-zinc-400">Briefs</div>
					<div class="space-y-1">
						{#each briefs as brief (brief.id)}
							<div class="flex gap-2">
								<button
									class="flex-1 rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-left text-xs hover:bg-zinc-800"
									onclick={() => selectBrief(brief)}
								>
									<div class="truncate">{brief.title ?? '（未命名）'}</div>
									<div class="mt-0.5 truncate text-[10px] text-zinc-500">{brief.id}</div>
								</button>
								<button
									class="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-xs text-red-200 hover:bg-red-950/60"
									onclick={() => deleteBriefFromUi(brief)}
								>
									删除
								</button>
							</div>
						{/each}
						{#if briefs.length === 0}
							<div class="text-xs text-zinc-500">暂无 briefs（可先用 API 创建）</div>
						{/if}
					</div>

					{#if selectedBrief}
						<div class="mt-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
							<div class="mb-2 text-xs font-semibold text-zinc-300">输出偏好（本 Brief 覆盖）</div>
							{#if globalOutputSpec}
								{@const effective = effectiveOutputSpec()}
								{#if effective}
									<div class="mb-2 text-[11px] text-zinc-500">
										Effective：{effective.language} · {effective.script_format}
										· 自动修复 {effective.max_fix_attempts} 次
										{#if effective.script_format_notes}
											· {effective.script_format_notes}
										{/if}
									</div>
								{/if}
							{/if}

							<div class="space-y-3 text-xs">
								<div class="grid grid-cols-[1fr_2fr] items-center gap-2">
									<label class="flex items-center gap-2 text-zinc-200">
										<input type="checkbox" bind:checked={overrideLanguage} />
										<span>覆盖语言</span>
									</label>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none disabled:opacity-60"
										placeholder="zh-CN"
										bind:value={briefLanguageDraft}
										disabled={!overrideLanguage || savingBriefPrefs}
									/>
								</div>

								<div class="grid grid-cols-[1fr_2fr] items-center gap-2">
									<label class="flex items-center gap-2 text-zinc-200">
										<input type="checkbox" bind:checked={overrideScriptFormat} />
										<span>覆盖剧本格式</span>
									</label>
									<select
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 disabled:opacity-60"
										bind:value={briefScriptFormatDraft}
										disabled={!overrideScriptFormat || savingBriefPrefs}
									>
										<option value="screenplay_int_ext">影视剧本（INT/EXT）</option>
										<option value="stage_play">舞台剧</option>
										<option value="custom">自定义</option>
									</select>
								</div>

								<div class="grid grid-cols-[1fr_2fr] items-start gap-2">
									<label class="flex items-center gap-2 pt-1 text-zinc-200">
										<input type="checkbox" bind:checked={overrideScriptNotes} />
										<span>覆盖备注</span>
									</label>
									<textarea
										class="w-full resize-none rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none disabled:opacity-60"
										rows="3"
										placeholder="可选：对 script_format 的补充说明"
										bind:value={briefScriptNotesDraft}
										disabled={!overrideScriptNotes || savingBriefPrefs}
									></textarea>
								</div>

								<div class="grid grid-cols-[1fr_2fr] items-center gap-2">
									<label class="flex items-center gap-2 text-zinc-200">
										<input type="checkbox" bind:checked={overrideMaxFixAttempts} />
										<span>覆盖自动修复次数</span>
									</label>
									<input
										class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs text-zinc-200 outline-none disabled:opacity-60"
										type="number"
										min="0"
										step="1"
										bind:value={briefMaxFixAttemptsDraft}
										disabled={!overrideMaxFixAttempts || savingBriefPrefs}
									/>
								</div>
							</div>

							<div class="mt-3 flex gap-2">
								<button
									class="flex-1 rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
									onclick={saveBriefPrefs}
									disabled={savingBriefPrefs}
								>
									保存覆盖
								</button>
								<button
									class="rounded-md bg-zinc-800 px-3 py-2 text-xs hover:bg-zinc-700 disabled:opacity-50"
									onclick={resetBriefPrefsToGlobal}
									disabled={savingBriefPrefs}
								>
									用全局
								</button>
							</div>
						</div>

						<div class="mt-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
							<div class="mb-2 flex items-center justify-between gap-2">
								<div class="text-xs font-semibold text-zinc-300">Brief 内容（结构化）</div>
								<button
									class="rounded-md bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700"
									onclick={() => (showBriefJson = !showBriefJson)}
								>
									{showBriefJson ? '收起' : '展开'}
								</button>
							</div>
							<div class="text-[10px] text-zinc-500">
								提示：对话补全出来的“简介/背景/人物”等都会写进 `brief.content`。
							</div>
							{#if showBriefJson}
								<div class="mt-2 text-[10px] text-zinc-500">
									最后更新：{new Date(selectedBrief.updated_at).toLocaleString()}
								</div>
								<pre
									class="mt-2 max-h-72 overflow-auto whitespace-pre-wrap text-[11px] text-zinc-300">
{JSON.stringify({ title: selectedBrief.title, content: selectedBrief.content }, null, 2)}</pre>
							{/if}
						</div>

						<div class="mt-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
							<div class="mb-2 text-xs font-semibold text-zinc-300">创建 Snapshot</div>
							<div class="flex gap-2">
								<input
									class="flex-1 rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600"
									placeholder="label（可空，如 v1 / draft）"
									bind:value={newSnapshotLabel}
									disabled={creatingSnapshot}
									onkeydown={(e) => e.key === 'Enter' && createNewSnapshot()}
								/>
								<button
									class="rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
									onclick={createNewSnapshot}
									disabled={creatingSnapshot}
								>
									创建
								</button>
							</div>
							<div class="mt-2 text-[10px] text-zinc-500">
								Snapshot 会固化当前 Brief，并写入生效的 output_spec（全局默认 + 本 Brief 覆盖）。
							</div>
						</div>

						<div class="mt-6">
							<div class="mb-2 text-xs font-semibold text-zinc-400">Snapshots</div>
							<div class="space-y-1">
								{#each briefSnapshots as snap (snap.id)}
									<div class="flex gap-2">
										<button
											class="flex-1 rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-left text-xs hover:bg-zinc-800"
											class:border-emerald-700={selectedSnapshot?.id === snap.id}
											onclick={() => selectSnapshot(snap)}
										>
											<div class="flex items-center justify-between">
												<div class="truncate">{snap.label ?? '（未命名）'}</div>
												<div class="text-[10px] text-zinc-500">
													{new Date(snap.created_at).toLocaleString()}
												</div>
											</div>
										</button>
										<button
											class="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-xs text-red-200 hover:bg-red-950/60"
											onclick={() => deleteSnapshotFromUi(snap)}
										>
											删除
										</button>
									</div>
								{/each}
								{#if briefSnapshots.length === 0}
									<div class="text-xs text-zinc-500">暂无 snapshots</div>
								{/if}
							</div>
						</div>

						{#if selectedSnapshot}
							<div class="mt-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
								<div class="mb-2 flex items-center justify-between gap-2">
									<div class="text-xs font-semibold text-zinc-300">Snapshot 内容</div>
									<button
										class="rounded-md bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700"
										onclick={() => (showSnapshotJson = !showSnapshotJson)}
									>
										{showSnapshotJson ? '收起' : '展开'}
									</button>
								</div>
								<div class="text-[10px] text-zinc-500">
									已选：{selectedSnapshot.label ?? '（未命名）'} ·
									{new Date(selectedSnapshot.created_at).toLocaleString()}
								</div>
								{#if showSnapshotJson}
									<pre
										class="mt-2 max-h-72 overflow-auto whitespace-pre-wrap text-[11px] text-zinc-300">
{JSON.stringify(selectedSnapshot.content, null, 2)}</pre>
								{/if}
							</div>

							<div class="mt-6 rounded-md border border-zinc-800 bg-zinc-900 p-3">
								<div class="mb-2 flex items-center justify-between gap-2">
									<div class="text-xs font-semibold text-zinc-300">KG / Lint</div>
									<button
										class="rounded-md bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700 disabled:opacity-50"
										onclick={refreshAnalysis}
										disabled={loadingAnalysis}
									>
										刷新
									</button>
								</div>

								<div class="mb-3 text-[11px] text-zinc-500">
									已选 Snapshot：{selectedSnapshot.label ?? '（未命名）'} ·
									{new Date(selectedSnapshot.created_at).toLocaleString()}
								</div>

								<div class="mb-5">
									<div class="mb-2 flex items-center justify-between gap-2">
										<div class="text-[11px] font-semibold text-zinc-400">
											Lint Issues（{lintIssues.length}）
										</div>
										<div class="flex items-center gap-2">
											<label class="flex items-center gap-1 text-[10px] text-zinc-400">
												<input type="checkbox" bind:checked={lintUseLlm} />
												<span>LLM</span>
											</label>
											<button
												class="rounded-md bg-emerald-700 px-2 py-1 text-[10px] font-semibold hover:bg-emerald-600 disabled:opacity-50"
												onclick={runLint}
												disabled={runningLint}
											>
												{runningLint ? '运行中…' : '运行'}
											</button>
										</div>
									</div>

									{#if lintIssues.length > 0}
										<div class="max-h-44 space-y-1 overflow-auto">
											{#each lintIssues as issue (issue.id)}
												<button
													class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-2 text-left text-xs hover:bg-zinc-800 disabled:opacity-60"
													onclick={() =>
														issue.artifact_version_id &&
														openArtifactVersionFromIssue(issue.artifact_version_id)}
													disabled={!issue.artifact_version_id}
												>
													<div class="flex items-center justify-between gap-2">
														<div class="truncate text-[11px] font-semibold text-zinc-200">
															{issue.severity} · {issue.code}
														</div>
														{#if issue.artifact_version_id}
															<div class="text-[10px] text-zinc-500">跳转</div>
														{/if}
													</div>
													<div class="mt-1 whitespace-pre-wrap text-[11px] text-zinc-300">
														{issue.message}
													</div>
												</button>
											{/each}
										</div>
									{:else}
										<div class="text-xs text-zinc-500">暂无 issues（可点击“运行”生成）。</div>
									{/if}
								</div>

								<div>
									<div class="mb-2 flex items-center justify-between gap-2">
										<div class="text-[11px] font-semibold text-zinc-400">
											KG Entities（{knowledgeGraph?.entities.length ?? 0}）
										</div>
										<button
											class="rounded-md bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700 disabled:opacity-50"
											onclick={rebuildKg}
											disabled={rebuildingKg}
										>
											{rebuildingKg ? '重建中…' : '重建'}
										</button>
									</div>

									{#if knowledgeGraph}
										{#if knowledgeGraph.entities.length > 0}
											<div class="max-h-44 space-y-1 overflow-auto">
												{#each knowledgeGraph.entities as ent (ent.id)}
													<div
														class="rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-1.5 text-xs"
													>
														<div class="flex items-center justify-between gap-2">
															<div class="truncate text-zinc-200">{ent.name}</div>
															<div class="text-[10px] text-zinc-500">
																{ent.entity_type}
															</div>
														</div>
													</div>
												{/each}
											</div>
										{:else}
											<div class="text-xs text-zinc-500">暂无实体（可点击“重建”）。</div>
										{/if}
									{:else}
										<div class="text-xs text-zinc-500">未加载。</div>
									{/if}
								</div>
							</div>

							<div class="mt-4 rounded-md border border-zinc-800 bg-zinc-900 p-3">
								<div class="mb-2 flex items-center justify-between gap-2">
									<div class="text-xs font-semibold text-zinc-300">Open Threads</div>
									<button
										class="rounded-md bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700 disabled:opacity-50"
										onclick={refreshAnalysis}
										disabled={loadingAnalysis}
									>
										刷新
									</button>
								</div>

								<div class="mb-4">
									<div class="mb-2 text-[11px] font-semibold text-zinc-400">新建线索</div>
									<div class="space-y-2">
										<input
											class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600"
											placeholder="标题（例如：神秘戒指）"
											bind:value={newThreadTitleDraft}
											disabled={creatingThread}
										/>
										<textarea
											class="w-full resize-none rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 disabled:opacity-60"
											rows="2"
											placeholder="描述（可选）"
											bind:value={newThreadDescriptionDraft}
											disabled={creatingThread}
										></textarea>
										<button
											class="w-full rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
											onclick={createThread}
											disabled={creatingThread || newThreadTitleDraft.trim().length === 0}
										>
											创建
										</button>
									</div>
								</div>

								<div class="mb-4">
									<div class="mb-2 text-[11px] font-semibold text-zinc-400">
										线索列表（{openThreads.length}）
									</div>
									{#if openThreads.length > 0}
										<div class="max-h-44 space-y-1 overflow-auto">
											{#each openThreads as t (t.id)}
												<button
													class="w-full rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-2 text-left text-xs hover:bg-zinc-800"
													class:border-emerald-700={selectedOpenThread?.id === t.id}
													onclick={() => selectOpenThread(t)}
												>
													<div class="flex items-center justify-between gap-2">
														<div class="truncate text-[11px] text-zinc-200">{t.title}</div>
														<div class="rounded bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-200">
															{t.status}
														</div>
													</div>
													{#if t.description}
														<div class="mt-1 line-clamp-2 text-[11px] text-zinc-400">
															{t.description}
														</div>
													{/if}
												</button>
											{/each}
										</div>
									{:else}
										<div class="text-xs text-zinc-500">暂无线索。</div>
									{/if}
								</div>

								{#if selectedOpenThread}
									<div class="rounded-md border border-zinc-800 bg-zinc-950/30 p-3 text-xs">
										<div class="mb-2 flex items-center justify-between gap-2">
											<div class="font-semibold text-zinc-200">{selectedOpenThread.title}</div>
											<button
												class="rounded-md bg-zinc-800 px-2 py-1 text-[10px] hover:bg-zinc-700"
												onclick={toggleSelectedThreadStatus}
											>
												{selectedOpenThread.status === 'closed' ? '重新打开' : '标记已回收'}
											</button>
										</div>
										{#if selectedOpenThread.description}
											<div class="mb-3 whitespace-pre-wrap text-[11px] text-zinc-300">
												{selectedOpenThread.description}
											</div>
										{/if}

										<div class="mb-2 text-[11px] font-semibold text-zinc-400">
											引用（{openThreadRefs.length}）
										</div>
										{#if openThreadRefs.length > 0}
											<div class="max-h-40 space-y-1 overflow-auto">
												{#each openThreadRefs as r (r.id)}
													<button
														class="w-full rounded-md border border-zinc-800 bg-zinc-900/60 px-2 py-2 text-left text-xs hover:bg-zinc-800"
														onclick={() => openArtifactVersionFromIssue(r.artifact_version_id)}
													>
														<div class="flex items-center justify-between gap-2">
															<div class="truncate text-[11px] text-zinc-200">
																{r.ref_kind} · {r.artifact_version_id}
															</div>
															<div class="text-[10px] text-zinc-500">跳转</div>
														</div>
														{#if r.quote}
															<div class="mt-1 line-clamp-2 text-[11px] text-zinc-400">
																{r.quote}
															</div>
														{/if}
													</button>
												{/each}
											</div>
										{:else}
											<div class="text-xs text-zinc-500">暂无引用。</div>
										{/if}

										<div class="mt-4">
											<div class="mb-2 text-[11px] font-semibold text-zinc-400">添加引用</div>
											<div class="space-y-2">
												<div class="flex gap-2">
													<input
														class="flex-1 rounded-md border border-zinc-800 bg-zinc-900 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600"
														placeholder="artifact_version_id"
														bind:value={refArtifactVersionIdDraft}
														disabled={addingThreadRef}
													/>
													<button
														class="rounded-md bg-zinc-800 px-2 py-2 text-[10px] hover:bg-zinc-700 disabled:opacity-50"
														onclick={useCurrentVersionForRef}
														disabled={!selectedArtifactVersion || addingThreadRef}
													>
														用当前
													</button>
												</div>
												<div class="flex gap-2">
													<select
														class="w-40 rounded-md border border-zinc-800 bg-zinc-900 px-2 py-2 text-xs text-zinc-200"
														bind:value={refKindDraft}
														disabled={addingThreadRef}
													>
														<option value="introduced">introduced</option>
														<option value="reinforced">reinforced</option>
														<option value="resolved">resolved</option>
													</select>
													<button
														class="flex-1 rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
														onclick={addThreadRef}
														disabled={addingThreadRef ||
															refArtifactVersionIdDraft.trim().length === 0}
													>
														添加
													</button>
												</div>
												<textarea
													class="w-full resize-none rounded-md border border-zinc-800 bg-zinc-900 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 disabled:opacity-60"
													rows="2"
													placeholder="quote（可选）"
													bind:value={refQuoteDraft}
													disabled={addingThreadRef}
												></textarea>
											</div>
										</div>
									</div>
								{/if}
							</div>

							<div class="mt-4 rounded-md border border-zinc-800 bg-zinc-900 p-3">
								<div class="mb-2 flex items-center justify-between gap-2">
									<div class="text-xs font-semibold text-zinc-300">导出 / 术语表</div>
								</div>

								<div class="mb-3 flex items-center justify-between gap-2">
									<label class="flex items-center gap-2 text-[11px] text-zinc-400">
										<input type="checkbox" bind:checked={applyGlossaryOnExport} />
										<span>导出时应用术语表</span>
									</label>
								</div>

								<div class="mb-4 grid grid-cols-3 gap-2">
									<button
										class="rounded-md bg-emerald-700 px-2 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
										onclick={downloadNovelMd}
										disabled={exportingNovelMd}
									>
										{exportingNovelMd ? '导出中…' : '小说 .md'}
									</button>
									<button
										class="rounded-md bg-emerald-700 px-2 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
										onclick={downloadNovelTxt}
										disabled={exportingNovelTxt}
									>
										{exportingNovelTxt ? '导出中…' : '小说 .txt'}
									</button>
									<button
										class="rounded-md bg-emerald-700 px-2 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
										onclick={downloadScriptFountain}
										disabled={exportingScriptFountain}
									>
										{exportingScriptFountain ? '导出中…' : '剧本 Fountain'}
									</button>
								</div>

								<div class="mb-2 text-[11px] font-semibold text-zinc-400">
									术语表（{glossaryEntries.length}）
								</div>

								{#if glossaryEntries.length > 0}
									<div class="mb-3 max-h-40 space-y-1 overflow-auto">
										{#each glossaryEntries as e (e.id)}
											<div
												class="rounded-md border border-zinc-800 bg-zinc-950/30 px-2 py-2 text-xs"
											>
												<div class="flex items-center justify-between gap-2">
													<div class="truncate text-[11px] text-zinc-200">{e.term}</div>
													<div class="text-[11px] text-zinc-400">→ {e.replacement}</div>
												</div>
											</div>
										{/each}
									</div>
								{:else}
									<div class="mb-3 text-xs text-zinc-500">暂无术语替换。</div>
								{/if}

								<div class="rounded-md border border-zinc-800 bg-zinc-950/30 p-3 text-xs">
									<div class="mb-2 text-[11px] font-semibold text-zinc-400">新增术语</div>
									<div class="space-y-2">
										<input
											class="w-full rounded-md border border-zinc-800 bg-zinc-900 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 disabled:opacity-60"
											placeholder="term（例如：旧城）"
											bind:value={glossaryTermDraft}
											disabled={creatingGlossaryEntry}
										/>
										<input
											class="w-full rounded-md border border-zinc-800 bg-zinc-900 px-2 py-2 text-xs text-zinc-200 outline-none placeholder:text-zinc-600 disabled:opacity-60"
											placeholder="replacement（例如：新城）"
											bind:value={glossaryReplacementDraft}
											disabled={creatingGlossaryEntry}
										/>
										<button
											class="w-full rounded-md bg-emerald-700 px-3 py-2 text-xs font-semibold hover:bg-emerald-600 disabled:opacity-50"
											onclick={addGlossary}
											disabled={creatingGlossaryEntry ||
												glossaryTermDraft.trim().length === 0 ||
												glossaryReplacementDraft.trim().length === 0}
										>
											{creatingGlossaryEntry ? '添加中…' : '添加'}
										</button>
									</div>
								</div>
							</div>
						{/if}
					{/if}

					{#if gapReport}
						<div class="mt-6">
							<div
								class="mb-2 flex items-center justify-between text-xs font-semibold text-zinc-400"
							>
								<span>Gap Report</span>
								<span class="rounded bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-200"
									>{gapReport.completeness}%</span
								>
							</div>

							{#if gapReport.conflict.length > 0}
								<div
									class="mb-2 rounded-md border border-red-900/40 bg-red-950/40 px-3 py-2 text-xs"
								>
									<div class="mb-1 font-semibold text-red-200">冲突</div>
									<ul class="list-disc space-y-0.5 pl-4 text-red-100">
										{#each gapReport.conflict as f (f)}
											<li>{f}</li>
										{/each}
									</ul>
								</div>
							{/if}

							{#if gapReport.missing.length > 0}
								<div
									class="mb-2 rounded-md border border-amber-900/40 bg-amber-950/30 px-3 py-2 text-xs"
								>
									<div class="mb-1 font-semibold text-amber-200">缺失</div>
									<ul class="list-disc space-y-0.5 pl-4 text-amber-100">
										{#each gapReport.missing as f (f)}
											<li>{f}</li>
										{/each}
									</ul>
								</div>
							{/if}

							{#if gapReport.questions.length > 0}
								<div class="rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-xs">
									<div class="mb-1 font-semibold text-zinc-300">追问</div>
									<ul class="list-disc space-y-0.5 pl-4 text-zinc-200">
										{#each gapReport.questions as q (q)}
											<li>{q}</li>
										{/each}
									</ul>
								</div>
							{/if}
						</div>
					{/if}

					<div class="mt-8 mb-3 text-xs font-semibold text-zinc-400">Artifacts</div>
					<div class="space-y-1">
						{#each artifacts as artifact (artifact.id)}
							<button
								class="flex w-full items-center justify-between rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-left text-xs hover:bg-zinc-800"
								onclick={() => selectArtifact(artifact)}
							>
								<span class="truncate">{artifact.title ?? artifact.kind}</span>
								<span class="ml-2 text-[10px] text-zinc-500">
									{artifact.ordinal ?? ''}
								</span>
							</button>
						{/each}
						{#if artifacts.length === 0}
							<div class="text-xs text-zinc-500">暂无 artifacts（可先用 API 创建）</div>
						{/if}
					</div>

					{#if selectedArtifact}
						<div class="mt-6">
							<div class="mb-2 text-xs font-semibold text-zinc-400">Versions</div>
							<div class="space-y-1">
								{#each artifactVersions as v (v.id)}
									<button
										class="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-left text-xs hover:bg-zinc-800"
										class:border-emerald-700={selectedArtifactVersion?.id === v.id}
										onclick={() => selectArtifactVersion(v)}
									>
										<div class="flex items-center justify-between">
											<div class="truncate">{v.source}</div>
											<div class="text-[10px] text-zinc-500">
												{new Date(v.created_at).toLocaleString()}
											</div>
										</div>
										<div class="mt-1 line-clamp-2 text-[11px] text-zinc-400">{v.content_text}</div>
									</button>
								{/each}
								{#if artifactVersions.length === 0}
									<div class="text-xs text-zinc-500">暂无 versions</div>
								{/if}
							</div>
						</div>
					{/if}
				</div>
			</section>
		</div>
	</div>
</div>
