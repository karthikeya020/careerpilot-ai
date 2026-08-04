# System Architecture

## Logical Architecture

```mermaid
flowchart TD
    UI[Career OS - Next.js] --> API[FastAPI API Gateway]
    API --> AUTH[Auth and RBAC]
    API --> CARE[CARE Engine]
    API --> TWIN[Career Twin Service]
    API --> TRUST[Trust Center]

    CARE --> SA[Single Specialist Path]
    CARE --> RET[Hybrid Retrieval Path]
    CARE --> MA[Multi-Agent Council]
    CARE --> REF[Reflection and Critic]
    CARE --> HR[Human Review Recommendation]

    RET --> VEC[Vector Retrieval]
    RET --> GRAPH[Neo4j GraphRAG]

    SA --> MODELS[LLM and ML Models]
    MA --> MODELS
    REF --> MODELS

    TWIN --> PG[(PostgreSQL)]
    VEC --> PGV[(pgvector)]
    GRAPH --> NEO[(Neo4j)]
    API --> REDIS[(Redis)]
    API --> OBJ[(Object Storage)]

    TRUST --> PG
    CARE --> OBS[Telemetry and Evaluation]
    OBS --> BENCH[Research Benchmark Lab]
```

## Primary Components

### Career OS Frontend
- Dashboard
- Career Twin graph
- Resume intelligence
- Assessment experience
- Interview Arena
- Experiment Lab
- Trust Center
- Research dashboard

### FastAPI Backend
- API validation
- Authentication
- Domain services
- WebSocket/SSE streaming
- File processing
- Agent orchestration

### CARE Engine
Calculates the minimum sufficient reasoning path based on evidence sufficiency, confidence, disagreement, risk, and task type.

### Career Twin Service
Maintains the current state and immutable update history for each student.

### Retrieval Layer
- pgvector: semantic retrieval
- Neo4j: relationship/path retrieval
- Hybrid ranker: combines graph and vector evidence

### Trust Layer
Stores evidence, confidence, provenance, reasoning summaries, decision traces, model versions, and review status.

## Deployment Topology

```mermaid
flowchart LR
    B[Browser] --> F[Frontend Container]
    F --> A[Backend Container]
    A --> P[(PostgreSQL + pgvector)]
    A --> N[(Neo4j)]
    A --> R[(Redis)]
    A --> S[(Object Storage)]
    A --> L[External or Local AI Models]
```
