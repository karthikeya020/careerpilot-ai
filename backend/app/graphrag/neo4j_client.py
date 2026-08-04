"""Neo4j driver factory. Every caller goes through `get_driver()` /
`is_graph_available()` -- nothing constructs a `neo4j.GraphDatabase.driver`
directly, so the relational-fallback behavior in app/graphrag/service.py has
one place to check availability.
"""

from functools import lru_cache

from neo4j import Driver, GraphDatabase

from app.core.config import get_settings


@lru_cache
def get_driver() -> Driver:
    settings = get_settings()
    return GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))


def is_graph_available() -> bool:
    try:
        driver = get_driver()
        driver.verify_connectivity()
        return True
    except Exception:
        return False


def close_driver() -> None:
    if get_driver.cache_info().currsize:
        get_driver().close()
        get_driver.cache_clear()
