"""Code Review Agent -- responsibility: review a solution the student pasted
for a LeetCode-style problem and return an interesting analysis: an overall
read, concrete improvements, and a clearly-stated time/space complexity.

Behind the provider abstraction like every other agent. The deterministic
fallback (used by the fake provider / when no API key is set) is a real
static heuristic over the source text -- loop-nesting depth, recursion,
sort calls, hash-structure use -- not a placeholder string.
"""

import json
import re
from typing import ClassVar

from app.agents.base import Agent, AgentInput, AgentOutput
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "code-review-v1"

_LOOP_RE = re.compile(r"\b(for|while)\b")
_SORT_RE = re.compile(r"\b(sort|sorted|sortBy|Collections\.sort|Arrays\.sort)\b")
_HASH_RE = re.compile(r"(\bset\(|\bdict\(|\{\}|HashMap|HashSet|unordered_map|unordered_set|new Map\(|new Set\()")
_RECURSION_HINT_RE = re.compile(r"\breturn\b[^\n]*\b(\w+)\s*\(")
_DEF_RE = re.compile(r"\b(def|function|public|private|static)\b[^\n(]*\b(\w+)\s*\(")


def _max_loop_nesting(code: str) -> int:
    """Deepest nesting of `for`/`while` -- brace depth for C-like source,
    indentation for Python-like. Sequential (non-nested) loops don't stack."""
    brace_style = code.count("{") >= 2 and code.count(";") >= 2
    best = 0

    if brace_style:
        depth = 0
        open_loops: list[int] = []
        for match in re.finditer(r"\bfor\b|\bwhile\b|[{}]", code):
            tok = match.group(0)
            if tok == "{":
                depth += 1
            elif tok == "}":
                depth -= 1
                open_loops = [d for d in open_loops if d < depth]
            else:
                open_loops.append(depth)
                best = max(best, len(open_loops))
        return best

    stack: list[int] = []
    for raw in code.splitlines():
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        while stack and indent <= stack[-1]:
            stack.pop()
        if re.match(r"(for|while)\b", raw.strip()):
            stack.append(indent)
            best = max(best, len(stack))
    return best


def _looks_recursive(code: str) -> bool:
    defined = {m.group(2) for m in _DEF_RE.finditer(code)}
    for m in _RECURSION_HINT_RE.finditer(code):
        if m.group(1) in defined:
            return True
    return bool(re.search(r"\b(dfs|recurse|helper|solve)\s*\([^)]*\)\s*[;+]?\s*(?:#|//|$)", code))


def _heuristic_review(request: StructuredChatRequest) -> dict:
    data = json.loads(request.messages[-1].content)
    code: str = data.get("code", "") or ""
    title: str = data.get("question_title", "this problem")
    how_to_think: str = data.get("how_to_think", "")
    line_count = len([ln for ln in code.splitlines() if ln.strip()])

    nesting = _max_loop_nesting(code)
    has_sort = bool(_SORT_RE.search(code))
    has_hash = bool(_HASH_RE.search(code))
    recursive = _looks_recursive(code)

    if nesting >= 3:
        time_complexity = f"O(n^{nesting})"
        complexity_explanation = f"{nesting} nested loops over the input dominate the runtime."
    elif nesting == 2:
        time_complexity = "O(n^2)"
        complexity_explanation = "A loop nested inside another loop over the input gives quadratic time."
    elif has_sort:
        time_complexity = "O(n log n)"
        complexity_explanation = "A sort of the input dominates; the rest looks linear."
    elif recursive:
        time_complexity = "O(n) to O(2^n)"
        complexity_explanation = (
            "Recursion detected -- linear if each element is visited once (tree/graph traversal, memoised DP), "
            "but exponential if the same subproblem is recomputed. Confirm whether results are cached."
        )
    elif nesting == 1:
        time_complexity = "O(n)"
        complexity_explanation = "A single pass over the input."
    else:
        time_complexity = "O(1) to O(n)"
        complexity_explanation = "No loops or recursion detected over the input; likely constant or bounded work."

    space_complexity = "O(n)" if has_hash or recursive else "O(1)"
    space_note = (
        "an auxiliary hash structure / recursion stack scales with the input"
        if space_complexity == "O(n)"
        else "only a constant number of scalars are kept"
    )

    strengths = []
    if has_hash:
        strengths.append("Uses a hash map/set to trade space for O(1) lookups instead of a nested scan.")
    if nesting <= 1 and not has_sort:
        strengths.append("Single pass -- no obvious redundant work over the input.")
    if line_count and line_count <= 25:
        strengths.append("Compact and readable at ~%d significant lines." % line_count)
    if not strengths:
        strengths.append("Solution is complete and follows a recognisable pattern for this problem type.")

    improvements = []
    if nesting >= 2:
        improvements.append(
            "The nested loop is the bottleneck. A hash map (seen-value -> index) or a sorted-two-pointer pass "
            "usually removes one level and gets this to O(n) or O(n log n)."
        )
    if recursive and "memo" not in code.lower() and "cache" not in code.lower():
        improvements.append("If subproblems repeat, add memoisation (a dict keyed by the recursion arguments) to avoid exponential blow-up.")
    if "return" not in code:
        improvements.append("No return statement found -- make sure the result is returned, not just printed.")
    improvements.append("Add the edge cases explicitly: empty input, single element, all-duplicates, and the target not present.")
    improvements.append("Name variables for their meaning (left/right/window_sum) so the invariant is self-documenting.")

    summary = (
        f"For {title}: this reads as a {time_complexity} solution. "
        + (strengths[0] if strengths else "")
        + f" Space is {space_complexity} because {space_note}."
    )

    return {
        "summary": summary,
        "strengths": strengths[:4],
        "improvements": improvements[:5],
        "time_complexity": time_complexity,
        "space_complexity": space_complexity,
        "complexity_explanation": complexity_explanation,
        "how_to_think": how_to_think or "Start from the brute force, then find and remove the repeated work.",
        "ai_generated": False,
    }


class CodeReviewInput(AgentInput):
    question_title: str
    concept_slug: str = ""
    how_to_think: str = ""
    language: str = ""
    code: str


class CodeReviewOutput(AgentOutput):
    summary: str = ""
    strengths: list[str] = []
    improvements: list[str] = []
    time_complexity: str = ""
    space_complexity: str = ""
    complexity_explanation: str = ""
    how_to_think: str = ""
    ai_generated: bool = False


class CodeReviewAgent(Agent[CodeReviewInput, CodeReviewOutput]):
    name = "code_review"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 20.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls = CodeReviewOutput

    def run(self, agent_input: CodeReviewInput) -> CodeReviewOutput:
        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="code_review",
            prompt_version=self.prompt_version,
            max_tokens=1200,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "You are a concise competitive-programming reviewer. Given a problem title and a candidate "
                        "solution, return: a short interesting `summary`, `strengths` (list), concrete `improvements` "
                        "(list), the `time_complexity` and `space_complexity` as tight Big-O strings, a one-paragraph "
                        "`complexity_explanation`, and `how_to_think` (the intuition to reach an optimal solution). "
                        "Set ai_generated to true."
                    ),
                ),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="CodeReviewOutput",
            deterministic_fn=_heuristic_review,
        )
        result = provider.complete_structured(request)
        parsed = result.parsed
        return CodeReviewOutput(
            confidence=0.5 if result.is_fallback else 0.8,
            evidence_ids=[],
            reasoning_summary=parsed.get("summary", ""),
            inference_type=result.inference_type,
            summary=parsed.get("summary", ""),
            strengths=parsed.get("strengths", []),
            improvements=parsed.get("improvements", []),
            time_complexity=parsed.get("time_complexity", ""),
            space_complexity=parsed.get("space_complexity", ""),
            complexity_explanation=parsed.get("complexity_explanation", ""),
            how_to_think=parsed.get("how_to_think", agent_input.how_to_think),
            ai_generated=bool(parsed.get("ai_generated", not result.is_fallback)),
        )
