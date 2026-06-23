"""Baseline security headers on every response (Phase 44 Step 3 / S-2)."""
from app.main import add_security_headers, _SECURITY_HEADERS


class _FakeResponse:
    def __init__(self):
        self.headers = {}


async def _call(request=None):
    async def fake_call_next(req):
        return _FakeResponse()

    return await add_security_headers(request, fake_call_next)


async def test_all_baseline_headers_present():
    response = await _call()
    for header, value in _SECURITY_HEADERS.items():
        assert response.headers[header] == value


async def test_hsts_includes_subdomains_and_long_max_age():
    response = await _call()
    hsts = response.headers["Strict-Transport-Security"]
    assert "includeSubDomains" in hsts
    assert "max-age=63072000" in hsts


async def test_csp_is_maximally_restrictive_for_api_only_backend():
    # This service never serves HTML/JS/CSS for a browser to apply CSP to in
    # normal operation -- "default-src 'none'" is a safety net for the
    # unexpected case (e.g. an error page slipping out), not a constraint
    # on any real feature.
    response = await _call()
    assert response.headers["Content-Security-Policy"] == "default-src 'none'"


async def test_x_content_type_options_is_nosniff():
    response = await _call()
    assert response.headers["X-Content-Type-Options"] == "nosniff"


async def test_x_frame_options_denies_framing():
    response = await _call()
    assert response.headers["X-Frame-Options"] == "DENY"
