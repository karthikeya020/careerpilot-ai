# Three-Minute Emergency Demo

Use when your slot is cut short, a judge asks for the fastest possible
version, or you're doing a hallway walk-up demo between sessions. Six
beats only: hook, Career Twin, GraphRAG, Experiment Lab, strongest
research result, closing. Everything below is the real, live product —
nothing staged, nothing pre-recorded.

**Setup**: `docker compose restart backend` for a fresh reset. One browser
tab, `/competition`, fullscreen (`F`). No second tab, no live clicks
outside Competition Mode — speed and reliability matter more than depth in
three minutes.

Competition Mode only moves one step at a time (`→`), so reaching steps 3,
5, 10, 11, and 14 means pressing `→` through the steps in between. Press
those extra times quickly and keep talking — don't stop to narrate them.

---

## 0:00–0:20 — Hook (20s)

**Screen**: step 1/14 "Opening" (already loaded).

**Clicks**: none yet.

**Say**:
> "Every career tool gives you a score with no explanation. CareerPilot AI
> shows its work — every number traced to real evidence, nothing
> invented."

**Click**: press `→` twice, quickly, while saying the transition line
below — you'll land on step 3.

**Say** (while pressing): "Meet Aanya, a real student account —"

---

## 0:20–0:50 — Career Twin (30s)

**Screen**: step 3/14 "Career Twin Awakening."

**Say**:
> "— and this is her Career Twin. 73% overall, but 36% confidence — the
> system telling you honestly it isn't fully sure yet. Portfolio readiness
> sits at 59% on just one evidence item, flagged low-sample, not padded.
> Every score here traces to stored evidence, or it says 'insufficient
> evidence.' Never a fabricated number."

**Click**: press `→` twice quickly to reach step 5, narrating through the
transition:

**Say** (while pressing): "So why is portfolio her weak spot? Not a guess —"

---

## 0:50–1:25 — GraphRAG (35s)

**Screen**: step 5/14 "GraphRAG Root Cause."

**Say**:
> "— a real graph traversal. Earlier, she answered a SQL question wrong.
> The system walked a real stored dependency graph: the question tests
> Inner Join. Inner Join depends on Joins. Joins depends on Table
> Relationships, which depends on the Relational Model — and her target
> role requires Inner Join. That whole chain came from a real Neo4j graph
> query — 'Graph retrieval used,' 60% confidence, honestly stated."

**Click**: press `→` five times quickly to reach step 10, narrating over
the jump:

**Say** (while pressing): "Now — what does she do about a gap like that?
Let's simulate it."

---

## 1:25–2:05 — Experiment Lab (40s)

**Screen**: step 10/14 "Career Experiment Lab."

**Say**:
> "This is her real Experiment Lab result — a deterministic, versioned
> simulation, not an LLM guessing. A balanced 30-hour study plan projects
> her from 73% to just over 75%. The formula accounts for diminishing
> returns, evidence diversity, her own historical trend, and her actual
> job description's requirements. And right on the card: 'personalized
> scenario estimate — not a guaranteed outcome or hiring prediction.' We
> never let this system predict whether she gets hired."

**Click**: press `→` once to reach step 11:

**Say** (while pressing): "And here's proof this beats a generic chatbot —"

---

## 2:05–2:40 — Strongest research result (35s)

**Screen**: step 11/14 "Research Proof."

**Say**:
> "— real experiments, run against the actual production system. CARE's
> adaptive routing matches expert judgment 100% of the time on our test
> set. A fixed single-agent baseline — what a simple chatbot wrapper would
> do — only gets 12.5%. And root-cause finding through our knowledge graph
> is 100% accurate by construction, because it follows a real stored
> dependency; pure vector-similarity search, the standard RAG approach,
> only finds the right answer half the time. That gap is why the graph
> exists."

**Click**: press `→` three times quickly to reach step 14:

**Say** (while pressing): "And this doesn't stop at one interview —"

---

## 2:40–3:00 — Closing (20s)

**Screen**: step 14/14 "Closing."

**Say**:
> "CareerPilot AI continuously learns how to guide every student toward
> their strongest possible career — never a fabricated score, never a
> hiring prediction. Your career, continuously evolving. Thank you."

**End state**: step 14/14. Ready for an immediate question.

---

## If a judge stops you mid-flow to ask a question

Answer it (see `JUDGE_Q_AND_A.md` for the 15-second version of every
common question), then resume exactly where you left off — Competition
Mode's step position doesn't move on its own, so nothing is lost.
