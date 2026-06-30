"""Phase 54: 7 analysis-output read endpoints (plus company lookup/search) were
made auth-required, closing a gap where anyone could read a full fraud-analysis
report for free, and where GET /company/{ticker} could trigger an unauthenticated
yfinance call + DB write on cache miss.

The per-route unit tests (test_analysis_history_endpoint.py etc.) call the route
function directly with a mocked db, proving the function's own logic works -- they
say nothing about whether Depends(get_current_user) is actually wired onto the live
route at the FastAPI/Starlette layer. This file exercises the real ASGI app via
TestClient to prove that.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db


async def _fake_db():
    # db: AsyncSession = Depends(get_db) is declared before current_user in every
    # gated route (matching the existing POST /run convention), so FastAPI opens
    # this dependency before get_current_user runs. A mocked session is harmless
    # here -- the route body, which would actually use it, is never reached
    # because get_current_user raises 401 first.
    yield AsyncMock()


@pytest.fixture
def client_no_auth():
    app.dependency_overrides[get_db] = _fake_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/v1/analysis/compare?tickers=AAPL,MSFT"),
    ("GET", "/api/v1/analysis/00000000-0000-0000-0000-000000000000/status"),
    ("GET", "/api/v1/analysis/company/AAPL"),
    ("GET", "/api/v1/analysis/company/AAPL/history"),
    ("GET", "/api/v1/report/company/AAPL"),
    ("GET", "/api/v1/company/AAPL"),
    ("GET", "/api/v1/company/search?q=AAPL"),
])
def test_route_requires_auth(client_no_auth, method, path):
    response = client_no_auth.request(method, path)

    assert response.status_code == 401
    # The global error envelope (Phase 5c) wraps every HTTPException, including
    # get_current_user's 401 -- not the plain `detail` string FastAPI uses by default.
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.json()["error"]["message"] == "Could not validate credentials"
