"""CLI entry point: `python -m app.graphrag.run_seed`.

Mirrors the relational concept/question/resource/skill tables into Neo4j.
Safe to run any time (every write is a MERGE) -- typically run once after
`alembic upgrade head` and again whenever the assessment taxonomy changes.
If Neo4j is unreachable this prints a clear message and exits 0 rather than
failing the demo startup sequence (Constitution rule 13).
"""

from app.core.db import SessionLocal
from app.graphrag.seed import seed_graph


def main() -> None:
    db = SessionLocal()
    try:
        counts = seed_graph(db)
    finally:
        db.close()

    if counts.get("skipped"):
        print(f"Graph seed skipped: {counts.get('reason')}")
        return
    print("Graph seeded successfully:")
    for key, value in counts.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
