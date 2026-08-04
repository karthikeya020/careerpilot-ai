# Career Knowledge Graph Schema

## Node Types

- Student
- Skill
- Concept
- Question
- Assessment
- Project
- ResumeEvidence
- JobRole
- Company
- JobDescription
- LearningResource
- InterviewQuestion
- Mission

## Relationship Types

```text
(Student)-[:HAS_SKILL_STATE]->(Skill)
(Skill)-[:CONTAINS_CONCEPT]->(Concept)
(Concept)-[:DEPENDS_ON]->(Concept)
(Question)-[:TESTS]->(Concept)
(Student)-[:ANSWERED]->(Question)
(Project)-[:DEMONSTRATES]->(Skill)
(ResumeEvidence)-[:SUPPORTS]->(Skill)
(JobRole)-[:REQUIRES]->(Skill)
(Company)-[:OFFERS]->(JobRole)
(JobDescription)-[:MENTIONS]->(Skill)
(LearningResource)-[:TEACHES]->(Concept)
(Mission)-[:TARGETS]->(Concept)
(InterviewQuestion)-[:EVALUATES]->(Skill)
```

## Root-Cause Query Example

**Question:** Why is SQL the student's highest-priority weakness?

Expected graph path:

```text
Student
→ low result on JOIN question
→ question tests table relationships
→ table relationships depend on relational algebra
→ skill required by selected Data Analyst role
→ skill appears in four target job descriptions
→ recommended resource teaches relational algebra and JOINs
```

## Hybrid Retrieval Strategy

1. Vector retrieval finds semantically relevant evidence.
2. Graph traversal finds dependencies and connected requirements.
3. Reranker scores evidence relevance, freshness, and reliability.
4. Response cites evidence IDs and graph paths.
