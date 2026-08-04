"""Supervisor Agent -- responsibility: given a task type, decide which
specialist agent(s) should handle it. A fixed, auditable dispatch table
(not a model call) -- this routing table is what CARE's executors consult
when wiring up a task, and it is deliberately simple/deterministic so it
never becomes a silent point of failure.
"""

from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput

_DISPATCH_TABLE: dict[str, list[str]] = {
    "resume_insight": ["resume_intelligence"],
    "ats_benchmark": ["ats_benchmark"],
    "assessment_grading": ["assessment"],
    "root_cause_analysis": ["graphrag"],
    "mission_synthesis": ["graphrag", "career_coach", "resource_recommendation"],
    "career_coach_synthesis": ["career_coach"],
    "resource_recommendation": ["resource_recommendation"],
    # Interview evaluation's *eligible* roster -- CARE's routing decision
    # (see app/services/interview_service.py) picks which subset of these
    # actually runs for a given answer, the same way root_cause_analysis
    # lists three eligible agents but a given execution may only invoke one.
    "interview_evaluation": [
        "communication",
        "hr",
        "technical",
        "resume_evidence",
        "jd_alignment",
        "critic",
        "consensus",
        "memory",
    ],
}


class SupervisorInput(AgentInput):
    task_type: str


class SupervisorOutput(AgentOutput):
    selected_agents: list[str] = Field(default_factory=list)


class SupervisorAgent(Agent[SupervisorInput, SupervisorOutput]):
    name = "supervisor"
    prompt_version = "supervisor-v1"
    timeout_seconds = 2.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls = SupervisorOutput

    def run(self, agent_input: SupervisorInput) -> SupervisorOutput:
        selected = _DISPATCH_TABLE.get(agent_input.task_type, [])
        return SupervisorOutput(
            confidence=1.0 if selected else 0.0,
            evidence_ids=[],
            reasoning_summary=(
                f"Task type '{agent_input.task_type}' dispatches to: {', '.join(selected) or 'no agent (unknown task type)'}."
            ),
            inference_type="deterministic_calculation",
            selected_agents=selected,
        )
