# Research Evaluation Plan

## Experiment A — Reasoning Architecture

Compare:

1. Single-agent baseline
2. Fixed multi-agent baseline
3. CARE adaptive routing

Metrics:

- Agreement with human rubric
- Accuracy/F1 where labels exist
- Cost per case
- Latency
- Failure rate
- Confidence calibration
- Human-review precision

## Experiment B — Retrieval

Compare:

1. Vector RAG
2. GraphRAG
3. Hybrid vector + graph retrieval

Metrics:

- Evidence recall@k
- Root-cause path accuracy
- Citation completeness
- Hallucination rate
- Latency

## Experiment C — Memory Ablation

Compare recommendations with and without Career Twin memory.

Metrics:

- Personalization score by human reviewers
- Repeated recommendation rate
- Goal consistency
- Evidence relevance

## Experiment D — Reflection Ablation

Compare first-pass evaluation with critic/reflection output.

Metrics:

- Rubric agreement
- Unsupported claim detection
- Score correction rate
- Added latency and cost

## Experiment E — Confidence Calibration

Metrics:

- Expected Calibration Error
- Brier score
- Accuracy by confidence bucket
- False high-confidence rate
- Human-review rate

## Experiment F — Student Improvement

Measure pre-intervention and post-intervention performance on targeted concepts.

Metrics:

- Assessment gain
- Retention gain
- Mission completion
- Time to improvement
- Student usefulness rating

## Dataset Strategy

- Create rubric-labeled synthetic and human-reviewed samples.
- Include easy, ambiguous, contradictory, and low-evidence cases.
- Keep a held-out competition demo set.
- Store prompt, model, rubric, and dataset versions.
