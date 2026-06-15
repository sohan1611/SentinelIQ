"""Global exception handlers (backend/app/main.py) emit {"error": {"code", "message"}}
for every error response, regardless of how the underlying exception's detail was
shaped at the raise site -- the Phase 5 fix for the analysis.py envelope/plain-string
inconsistency (OPUS Phase 5 scope, CLAUDE.md Error Handling rule 6).
"""

import json

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from app.main import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)


def _body(response):
    return json.loads(response.body)


async def test_http_exception_with_plain_string_detail_is_wrapped():
    exc = HTTPException(status_code=404, detail="Analysis not found")
    response = await http_exception_handler(None, exc)

    assert response.status_code == 404
    assert _body(response) == {"error": {"code": "NOT_FOUND", "message": "Analysis not found"}}


async def test_http_exception_with_envelope_detail_passes_through_unchanged():
    detail = {"error": {"code": "LIMIT_REACHED", "message": "Monthly analysis limit reached. Upgrade to Pro."}}
    exc = HTTPException(status_code=403, detail=detail)
    response = await http_exception_handler(None, exc)

    assert response.status_code == 403
    assert _body(response) == detail


async def test_http_exception_unmapped_status_falls_back_to_generic_code():
    exc = HTTPException(status_code=401, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    response = await http_exception_handler(None, exc)

    assert response.status_code == 401
    assert _body(response) == {"error": {"code": "UNAUTHORIZED", "message": "Could not validate credentials"}}
    assert response.headers["www-authenticate"] == "Bearer"


async def test_http_exception_truly_unmapped_status_uses_http_error_code():
    exc = HTTPException(status_code=418, detail="I'm a teapot")
    response = await http_exception_handler(None, exc)

    assert response.status_code == 418
    assert _body(response) == {"error": {"code": "HTTP_ERROR", "message": "I'm a teapot"}}


async def test_http_exception_409_maps_to_conflict_code():
    # watchlist.py raises a plain-string 409 for duplicate entries.
    exc = HTTPException(status_code=409, detail="Company already in watchlist")
    response = await http_exception_handler(None, exc)

    assert response.status_code == 409
    assert _body(response) == {"error": {"code": "CONFLICT", "message": "Company already in watchlist"}}


async def test_validation_exception_handler_shape():
    exc = RequestValidationError(errors=[{"loc": ("body", "ticker"), "msg": "Field required", "type": "missing"}])
    response = await validation_exception_handler(None, exc)

    assert response.status_code == 422
    body = _body(response)
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "ticker" in body["error"]["message"]


async def test_unhandled_exception_handler_hides_internal_details():
    exc = RuntimeError("db connection string leaked: postgresql://user:pass@host/db")
    response = await unhandled_exception_handler(None, exc)

    assert response.status_code == 500
    body = _body(response)
    assert body == {"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}}
    assert "postgresql://" not in json.dumps(body)
