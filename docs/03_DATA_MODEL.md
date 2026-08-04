# Core Data Model

## Main Entities

| Entity | Purpose |
|---|---|
| User | Identity, role, account state |
| StudentProfile | Goals, preferences, target roles |
| CareerTwin | Current aggregate intelligence state |
| CareerTwinVersion | Immutable state snapshots |
| Skill | Skill taxonomy |
| Concept | Skill-level dependency concept |
| SkillState | Student score, confidence, trend |
| Evidence | Resume, assessment, interview, project, or activity proof |
| Resume | Uploaded resume and parsed structure |
| JobDescription | Target role/company requirements |
| Assessment | Assessment definition |
| AssessmentAttempt | Student completion record |
| QuestionResponse | Answer and concept-level result |
| Interview | Interview session |
| InterviewResponse | Timestamped response and transcript |
| AgentEvaluation | Specialist score, evidence, confidence |
| Mission | Daily/weekly improvement activity |
| Resource | Learning material |
| Scenario | Experiment Lab simulation |
| DecisionTrace | End-to-end AI decision provenance |
| ConfidenceRecord | Confidence inputs and calibration data |

## Score Integrity Rule

A `SkillState.score` may only be updated through a recorded `Evidence` item and a stored scoring rule/version.

## Career Twin Update Example

```json
{
  "student_id": "demo-student",
  "skill": "SQL JOINs",
  "old_score": 0.43,
  "new_score": 0.58,
  "confidence": 0.84,
  "evidence_ids": ["assessment-14", "interview-6"],
  "scoring_rule_version": "skill-score-v1",
  "reason": "Follow-up assessment accuracy improved and explanation quality increased.",
  "requires_human_review": false
}
```
