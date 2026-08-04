# Phase 2 Execution Plan — AI Intelligence Core

## 0. Phase 1 validation (done before writing this plan)

- `pytest -q` → 28/28 passed (native SQLite venv).
- `npx tsc --noEmit` → clean. `npm run lint` → clean.
- `docker compose ps` → postgres/redis/neo4j healthy, backend/frontend running
  (stack left running from the Docker/Postgres smoke-test session).
- No regressions found. Phase 1 is accepted as a real foundation, not merely
  because the report claims it — the above commands were re-run, not assumed.

## 1. Scope reality check

The prompt asks for a full multi-agent, GraphRAG, adaptive-assessment,
autonomous-improvement research platform. Building every listed item at
production depth in one pass is not achievable honestly. The approach taken
here: **build every subsystem for real, at a deliberately scoped depth, wired
into one genuine end-to-end loop that satisfies every numbered acceptance
criterion with actual passing tests** — not stubs that merely compile, and
not narrative claims unbacked by code.

Where a scope cut is made, it is stated explicitly below and in the
completion report, not hidden.

## 2. Architectural decisions

### 2.1 AI provider layer (`app/ai/`)
- `ChatProvider` / `EmbeddingProvider` / `RerankerProvider` protocols.
- `FakeChatProvider`: does **not** pretend to be an LLM producing free text.
  Each agent supplies a deterministic derivation function; `FakeChatProvider`
  executes it and attaches fake-but-consistent latency/token/cost metadata
  and `inference_type="deterministic_calculation"`. This is more honest than
  simulating natural-language generation, and it is what makes the whole
  system testable and demoable without any API key.
- `AnthropicChatProvider`: real adapter used only when
  `PRIMARY_LLM_API_KEY` is set; retries + timeout + structured-output
  validation (ask for JSON, validate against the agent's Pydantic schema,
  one repair retry on failure), tags results `inference_type="model_inference"`.
  Never exercised by the test suite (no key in CI/sandbox) — this satisfies
  "tests must not require paid API access" while keeping the adapter real,
  not a placeholder.
- `HashingEmbeddingProvider`: deterministic feature-hashing embedding
  (tokenize → hash each token into a fixed 128-dim vector → normalize). This
  is a legitimate, dependency-free embedding technique, not a random stand-in
  — texts sharing vocabulary really do end up closer in cosine distance.
- `get_chat_provider()` / `get_embedding_provider()` / `get_reranker()` in
  `app/ai/registry.py` are the only place business logic touches provider
  selection — swapping providers never touches callers (Constitution rule 9).

### 2.2 Vector storage — scope cut, documented
`pgvector` is available on the Postgres image, but the whole backend runs
identically against SQLite in this sandbox (Phase 1's cross-dialect design).
Introducing a native `VECTOR` column would break that guarantee. Instead:
embeddings are stored as JSON float arrays via the existing `JSONBType`, and
cosine similarity is computed in Python at query time. At current demo scale
(dozens–hundreds of chunks) this is fast and fully correct; a native
`pgvector` ANN index is listed as a Phase 3 performance upgrade, not a
correctness requirement.

### 2.3 Knowledge graph — SQL is the source of truth, Neo4j is the traversal/visualization layer
A relational `Concept` / `ConceptDependency` table pair is the authoritative
store for concept prerequisite relationships (always available, no external
dependency, satisfies Constitution rule 1 — every value traceable to stored
data). The same relationships are mirrored into Neo4j at seed time so the
GraphRAG agent can do real Cypher traversal and the graph-visualization API
has real graph data to serve. If Neo4j is unreachable, root-cause analysis
falls back to computing the identical path from the SQL adjacency table and
labels the response `graph_source: "relational_fallback"` instead of
`"neo4j"` — a real, tested, deterministic fallback (Constitution rule 13),
not a silent failure.

### 2.4 CARE Engine
Implements the exact routing table from `docs/05_CARE_ENGINE_SPEC.md`:
insufficient evidence → GraphRAG retrieval; confidence ≥ 0.80 with sufficient
evidence → single specialist; conflicting evidence or confidence < 0.55 →
multi-agent council; disagreement > 0.20 → critic/reflection; final
confidence < 0.50 → human-review recommendation; a pure deterministic
calculation never invokes an agent at all. Every decision is persisted as a
`CareExecution` row (request, factors, route, agents invoked, confidence,
cost, latency, policy version) — this is the Trust Center's data source.

### 2.5 Ten specialist agents — real but intentionally simple internals
Every agent is a real class with typed Pydantic input/output, a prompt
version, a timeout, defined failure behavior, a confidence output, and
evidence citations — and a test. Several agents' internal logic is
deterministic rule-based rather than LLM-prompted (ATS benchmark, resource
ranking, critic, consensus, memory) because that is what makes them
correct, fast, and free to run in CI — matching Constitution rule 9. Agents
that plausibly benefit from generative synthesis (resume insight summary,
mission rationale, free-text assessment grading) go through the provider
abstraction, so a live model genuinely improves them without changing
callers. **No agent writes to the Career Twin directly** — all mutation goes
through `career_twin/scoring.py::recompute_twin`, unchanged from Phase 1.

### 2.6 Assessment engine
Two domains seeded as a data migration (matching the Phase 1 roles/skills
precedent): **SQL** (14 questions: relational model, table relationships,
inner/outer join, group by, aggregates, where vs having, subqueries,
indexes, normalization) and **Python** (10 questions: types, comprehensions,
functions, exceptions, dict operations). Concept dependency chain matches
`docs/04_KNOWLEDGE_GRAPH.md`'s example exactly: `relational_model →
table_relationships → joins → inner_join / outer_join`. MCQ/multi-select
scored deterministically; short-answer/concept-explanation graded via the AI
evaluator behind the provider abstraction (keyword-overlap fallback when the
fake provider is active). Adaptive selection considers concept dependency
order and running accuracy. Labeled throughout as an **adaptive educational
assessment prototype** — no psychometric validity claim.

### 2.7 Autonomous improvement loop
`app/services/autonomous_loop_service.py` implements
Observe → Diagnose → Plan → Teach → Assess → Reflect → Update Twin → Next
mission, wired to the real CARE engine, GraphRAG agent, career coach agent,
and resource recommendation agent — not a narrative description. This is
exercised end-to-end by the required deterministic test (`docs` §
"Required deterministic end-to-end test"), reusing the demo student's seeded
weak-SQL-JOIN evidence.

### 2.8 What is explicitly deferred (not built) in Phase 2
- Native pgvector ANN indexing (Python cosine similarity is correct at this
  scale — see §2.2).
- Interview Arena, Experiment Lab full UI (backend scaffold packages remain
  empty; out of the 20 acceptance criteria, none require them).
- Fine-grained per-student learning-preference modeling (resource ranking
  uses role/level/time/dependency, not a preference model — no evidence
  source exists yet for preferences).
- A second live LLM provider (only Anthropic adapter + fake; the interface
  supports a second one, but wiring an actual second SDK with no second key
  available would be unused code).

## 3. New database migrations

1. Schema migration adding: `assessment_domains`, `concepts`,
   `concept_dependencies`, `questions`, `assessment_attempts`,
   `question_responses`, `resources`, `care_executions`, `agent_runs`,
   `retrieval_documents`, `evaluation_runs`, `evaluation_results`; plus new
   columns `skill_evidence.concept_id`, and on `learning_missions`: `tasks`,
   `estimated_minutes`, `root_cause`, `expected_impact_estimate`,
   `expected_impact_confidence`, `resource_ids`, `outcome_evidence_ids`,
   `actual_observed_change`.
2. Data migration seeding: SQL + Python concepts/dependencies/questions, and
   the resource catalog — using the real `GUID`/`JSONBType` decorators from
   the start (the Phase 1 Postgres bug is now a known pitfall, not repeated).

Both will be verified `upgrade`/`downgrade`/`check` on SQLite (fast local
loop) and then re-verified against the real Postgres container before Phase
2 is called done, exactly as the Docker/Postgres smoke test did for Phase 1.

## 4. Implementation order

AI provider layer → new models/migrations → CARE engine → agents → graph
(Neo4j + relational mirror) → hybrid retrieval → assessment engine →
resource catalog → Career Twin assessment-component wiring → autonomous
loop → Trust Center API + UI → research instrumentation → seed-demo update
(give the demo student a failed SQL JOIN attempt) → full test suite → Docker
rebuild + Postgres re-verification → docs.

## 5. Definition of done for this phase

Every one of the 20 acceptance criteria in the prompt has a corresponding
passing automated test or a live-verified API/UI call, listed explicitly in
`PHASE_2_COMPLETION_REPORT.md` — not asserted without evidence.
