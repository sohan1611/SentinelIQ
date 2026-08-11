"""Unit tests for Phase 66 narrative statement source selection."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import app.tasks.analysis_worker as analysis_worker


def _statement(period: str, text: str, source: str = "SEC 10-Q") -> dict:
    return {"period": period, "text": text, "source": source}


def _context() -> analysis_worker.StageContext:
    session = AsyncMock()
    # AsyncSession.add() is synchronous even though commit()/rollback() are not.
    session.add = MagicMock()
    return analysis_worker.StageContext(
        analysis_id=uuid4(),
        company_id=uuid4(),
        log=MagicMock(),
        session=session,
        company=SimpleNamespace(name="Acme Corp", ticker="ACME"),
    )


def _patch_engine(monkeypatch) -> MagicMock:
    engine = MagicMock()
    engine.analyze = AsyncMock(return_value=(73.0, [], [], []))
    monkeypatch.setattr(analysis_worker, "ConsistencyEngine", lambda: engine)
    return engine


async def test_uses_edgar_statements_without_news_fallback(monkeypatch):
    ctx = _context()
    edgar_statements = [
        _statement("2026-06-30", "Revenue increased on stronger demand."),
        _statement("2026-03-31", "Margins improved through lower costs."),
    ]
    fetch_edgar = AsyncMock(return_value=edgar_statements)
    fetch_news = AsyncMock()
    monkeypatch.setattr(analysis_worker, "fetch_management_statements", fetch_edgar)
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", fetch_news)
    engine = _patch_engine(monkeypatch)

    await analysis_worker._stage_narrative(ctx)

    assert fetch_edgar.await_args.args == ("ACME",)
    assert fetch_edgar.await_args.kwargs == {
        "limit": analysis_worker.NARRATIVE_EDGAR_FILING_LIMIT,
    }
    assert fetch_news.await_count == 0
    assert ctx.narrative_source == "edgar_mdna"
    assert engine.analyze.await_args.args == ("Acme Corp", edgar_statements)


async def test_falls_back_to_news_when_edgar_has_fewer_than_two_statements(monkeypatch):
    ctx = _context()
    fetch_edgar = AsyncMock(return_value=[_statement("2026-06-30", "Only one MD&A excerpt.")])
    news_statements = [
        _statement("2026-08-01", "Headline one.", "News"),
        _statement("2026-08-02", "Headline two.", "News"),
    ]
    fetch_news = AsyncMock(return_value=news_statements)
    monkeypatch.setattr(analysis_worker, "fetch_management_statements", fetch_edgar)
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", fetch_news)
    engine = _patch_engine(monkeypatch)

    await analysis_worker._stage_narrative(ctx)

    assert fetch_news.await_args.args == ("Acme Corp", "ACME")
    assert fetch_news.await_args.kwargs == {"limit": 2}
    assert ctx.narrative_source == "news_headlines"
    assert engine.analyze.await_args.args == ("Acme Corp", news_statements)


async def test_falls_back_to_news_when_edgar_fetch_raises(monkeypatch):
    ctx = _context()
    fetch_edgar = AsyncMock(side_effect=RuntimeError("EDGAR unavailable"))
    news_statements = [
        _statement("2026-08-01", "Headline one.", "News"),
        _statement("2026-08-02", "Headline two.", "News"),
    ]
    fetch_news = AsyncMock(return_value=news_statements)
    monkeypatch.setattr(analysis_worker, "fetch_management_statements", fetch_edgar)
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", fetch_news)
    engine = _patch_engine(monkeypatch)

    await analysis_worker._stage_narrative(ctx)

    assert fetch_news.await_count == 1
    assert ctx.log.warning.call_count == 1
    assert ctx.narrative_source == "news_headlines"
    assert engine.analyze.await_args.args == ("Acme Corp", news_statements)


async def test_sets_neutral_none_source_when_both_sources_have_fewer_than_two_statements(monkeypatch):
    ctx = _context()
    fetch_edgar = AsyncMock(return_value=[])
    fetch_news = AsyncMock(return_value=[_statement("2026-08-01", "Only one headline.", "News")])
    monkeypatch.setattr(analysis_worker, "fetch_management_statements", fetch_edgar)
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", fetch_news)
    engine = _patch_engine(monkeypatch)

    await analysis_worker._stage_narrative(ctx)

    assert ctx.scores["narrative"] == 50.0
    assert ctx.narrative_source == "none"
    assert engine.analyze.await_count == 0


async def test_truncates_edgar_statement_copy_without_mutating_cached_source(monkeypatch):
    ctx = _context()
    original_text = "x" * (analysis_worker.NARRATIVE_MAX_STATEMENT_CHARS + 1)
    edgar_statements = [
        _statement("2026-06-30", original_text),
        _statement("2026-03-31", "A shorter MD&A excerpt."),
    ]
    fetch_edgar = AsyncMock(return_value=edgar_statements)
    fetch_news = AsyncMock()
    monkeypatch.setattr(analysis_worker, "fetch_management_statements", fetch_edgar)
    monkeypatch.setattr(analysis_worker, "fetch_news_statements", fetch_news)
    engine = _patch_engine(monkeypatch)

    await analysis_worker._stage_narrative(ctx)

    received_statements = engine.analyze.await_args.args[1]
    assert len(received_statements[0]["text"]) == analysis_worker.NARRATIVE_MAX_STATEMENT_CHARS
    assert received_statements[0]["text"] == original_text[:analysis_worker.NARRATIVE_MAX_STATEMENT_CHARS]
    assert received_statements[0] is not edgar_statements[0]
    assert edgar_statements[0]["text"] == original_text
    assert fetch_news.await_count == 0
