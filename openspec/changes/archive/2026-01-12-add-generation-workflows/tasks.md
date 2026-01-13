## 1. Implementation
- [x] 1.1 Add workflow execution endpoints (`/next`, `/pause`, `/resume`) and step cursor in run state
- [x] 1.2 Add prompt templates for novel/script planners, writers, critics (versioned files)
- [x] 1.3 Implement novel workflow (outline → beats → chapter draft → commit + dual digests + state update)
- [x] 1.4 Implement script workflow (scene list → scene draft → commit), honoring `output_spec.script_format`
- [x] 1.5 Add pgvector memory store (chunk table + embeddings) and retrieval step integration
- [x] 1.6 Add critic rubric + fix loop (hard/soft checks, targeted rewrites)
- [x] 1.7 Update web UI to run workflows stepwise and show step artifacts + digests
- [x] 1.8 Add tests: workflow step transitions, state invariants, RAG retrieval, critic gating

## 2. Validation
- [x] 2.1 `openspec validate add-generation-workflows --strict`
- [x] 2.2 Backend: `ruff` + `pytest`
- [x] 2.3 Frontend: `npm run lint` + `npm run check`
