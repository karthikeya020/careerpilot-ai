# Product Requirements Document

## 1. Primary Users

### Student
Uploads evidence, selects career goals, completes assessments, attends interviews, receives missions, explores scenarios, and tracks improvement.

### Faculty/Placement Reviewer — later phase
Reviews aggregate progress and low-confidence cases without exposing harmful public rankings.

### Administrator
Manages rubrics, knowledge resources, job-role templates, system health, models, and evaluation datasets.

## 2. Core Functional Requirements

### FR-01 Authentication and Profile
- Secure registration and login
- Role-based access
- Student career goal and target-role profile
- Consent and data preferences

### FR-02 Career OS
- Overall readiness
- Career Twin confidence
- Today's mission
- Priority weakness and root cause
- Weekly roadmap
- Recent evidence and score changes
- Upcoming interview
- Experiment Lab shortcut

### FR-03 Career Twin
- Store skills, concepts, confidence, goals, evidence, assessments, interviews, and progress
- Version every meaningful update
- Explain why each score changed
- Keep a timeline of student evolution

### FR-04 Resume and ATS Intelligence
- Upload and parse resume
- Extract skills, projects, experience, education, and measurable evidence
- Compare against target job descriptions
- Identify missing, weak, and unsupported evidence
- Provide section-level heatmaps

### FR-05 Assessments
- Baseline role assessment
- Adaptive question selection
- Concept-level scoring
- Question difficulty and evidence storage
- Follow-up reassessment after learning missions

### FR-06 GraphRAG
- Represent skill and concept dependencies
- Link questions, resources, roles, companies, projects, and evidence
- Retrieve paths explaining root causes
- Support vector + graph hybrid retrieval

### FR-07 CARE Engine
- Route simple tasks to one specialist
- Escalate insufficient-evidence cases to retrieval
- Escalate conflicts to multiple evaluators
- Trigger reflection when disagreement is high
- Recommend human review when uncertainty remains

### FR-08 Interview Arena
- Voice or text interview
- HR and technical question generation
- Transcription
- Specialist evaluation
- Evidence validation against resume/profile
- Replay timeline with actionable feedback

### FR-09 Autonomous Coach
- Detect priority weakness
- Generate daily mission and weekly roadmap
- Recommend targeted resources
- Schedule reassessment
- Update Career Twin after completion

### FR-10 Career Experiment Lab
- Compare alternative learning allocations
- Estimate readiness change
- Display confidence and evidence
- Clearly label outputs as scenario estimates

### FR-11 Trust Center
- Confidence score
- Evidence ledger
- Agent/model provenance
- Agreement/disagreement
- Graph path
- Human-review status
- Decision trace

### FR-12 Research Lab
- Single-agent vs fixed multi-agent vs CARE
- Vector RAG vs GraphRAG vs hybrid
- Memory vs no memory
- Reflection vs no reflection
- Latency, cost, accuracy, calibration, agreement

## 3. Quality Requirements

- Responsive premium UI
- Structured AI output validation
- Graceful failure handling
- Cached demo mode
- Audit logging
- Prompt/model versioning
- Security and privacy controls
- Deterministic fallback for core demo flow

## 4. Explicit Exclusions

- Fake experience generation
- Public student ranking
- Hiring probability claims
- Lie detection
- Automated cheating in assessments
- Unsupported emotion or personality inference
- Resume content fabrication
