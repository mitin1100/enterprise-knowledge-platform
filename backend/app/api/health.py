from fastapi import APIRouter
from elasticsearch import Elasticsearch
from redis import Redis

from app.core.config import settings
# from app.db.session import check_database


router = APIRouter(tags=['health'])

@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.APP_NAME,
    }

# @router.get("/health/dependencies")
# def dependency_health_check() -> dict[str, object]:
#     checks: dict[str, str] = {}

#     try:
#         check_database()
#         checks["postgres"] = "ok"
#     except Exception as exc:
#         checks["postgres"] = (
#             f"error: {type(exc).__name__}: {str(exc)}"
#         )

#     try:
#         elasticsearch_client = Elasticsearch(
#             settings.elasticsearch_url
#         )

#         if elasticsearch_client.info():
#             checks["elasticsearch"] = "ok"
#         else:
#             checks["elasticsearch"] = (
#                 "error: ping returned False"
#             )

#     except Exception as exc:
#         checks["elasticsearch"] = (
#             f"error: {type(exc).__name__}: {str(exc)}"
#         )

#     healthy = all(
#         value == "ok" for value in checks.values()
#     )
#     print(checks)

#     return {
#         "status": "ok" if healthy else "degraded",
#         "checks": checks,
#     }
