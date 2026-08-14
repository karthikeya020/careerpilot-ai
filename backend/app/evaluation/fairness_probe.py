"""Fairness probe: scores semantically-equivalent answer pairs that differ
only in phrasing style (formal/native-sounding vs. casual/non-native-sounding
patterns) through the real TechnicalAgent, and reports the measured score
deltas. This is strictly a measurement of *scoring-function* sensitivity to
surface form -- never a claim of being bias-free, and never an inference
about any student's identity, background, or ability (Constitution rule 8:
no unsupported psychological/personal inference). A nonzero delta is a real,
disclosed limitation to track, not a verdict on anyone.
"""

from app.agents.technical_agent import TechnicalAgent, TechnicalInterviewInput

FAIRNESS_PROBE_VERSION = "fairness-probe-v1"

FAIRNESS_DISCLAIMER = (
    "These are measured score deltas for semantically-equivalent answers that differ only in phrasing style -- "
    "not a claim that this scoring function is bias-free, and never an inference about any student's identity, "
    "background, or ability. A nonzero delta means the current keyword/depth-cue heuristic is sensitive to "
    "phrasing; that is a disclosed limitation to track, not a verdict."
)

_FAIRNESS_PAIRS = [
    {
        "pair_id": "index-tradeoffs-phrasing",
        "question_prompt": "Explain the tradeoffs of adding a database index.",
        "expected_keywords": ["index", "trade-off", "overhead"],
        "variant_a_label": "formal phrasing",
        "variant_a_transcript": (
            "The trade-off of adding an index is faster reads at the cost of write overhead, because every "
            "insert also has to update the index."
        ),
        "variant_b_label": "non-native-pattern phrasing",
        "variant_b_transcript": (
            "Index is making read more fast, but write become slow because index also need update every time, "
            "this is the trade-off."
        ),
    },
    {
        "pair_id": "normalization-phrasing",
        "question_prompt": "What is database normalization?",
        "expected_keywords": ["redundancy", "foreign key", "normalization"],
        "variant_a_label": "formal phrasing",
        "variant_a_transcript": (
            "Normalization reduces redundancy by splitting data into related tables connected through foreign keys."
        ),
        "variant_b_label": "non-native-pattern phrasing",
        "variant_b_transcript": "Normalization is for reduce redundancy, table is split and connect using foreign key, this way.",
    },
]


def run_fairness_probe() -> dict:
    rows = []
    for pair in _FAIRNESS_PAIRS:
        out_a, _latency = TechnicalAgent().safe_run(
            TechnicalInterviewInput(
                question_prompt=pair["question_prompt"], transcript=pair["variant_a_transcript"], expected_keywords=pair["expected_keywords"]
            )
        )
        out_b, _latency = TechnicalAgent().safe_run(
            TechnicalInterviewInput(
                question_prompt=pair["question_prompt"], transcript=pair["variant_b_transcript"], expected_keywords=pair["expected_keywords"]
            )
        )
        rows.append(
            {
                "pair_id": pair["pair_id"],
                "variant_a_label": pair["variant_a_label"],
                "variant_a_confidence": out_a.confidence,
                "variant_a_correctness": out_a.correctness_score,
                "variant_b_label": pair["variant_b_label"],
                "variant_b_confidence": out_b.confidence,
                "variant_b_correctness": out_b.correctness_score,
                "confidence_delta": round(out_a.confidence - out_b.confidence, 4),
                "correctness_delta": round(out_a.correctness_score - out_b.correctness_score, 4),
            }
        )

    max_abs_delta = round(max((abs(r["correctness_delta"]) for r in rows), default=0.0), 4)
    return {
        "engine_version": FAIRNESS_PROBE_VERSION,
        "pair_count": len(rows),
        "rows": rows,
        "max_absolute_correctness_delta": max_abs_delta,
        "disclaimer": FAIRNESS_DISCLAIMER,
    }
