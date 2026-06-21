from app.core.forensics.restatement_detector import detect_restatements


def test_no_divergence_produces_no_flags(make_edgar_fact):
    facts = [
        make_edgar_fact("Assets", "2023-12-31", 1000.0, form="10-K", filed="2024-01-15", accn="a1"),
        make_edgar_fact("Assets", "2023-12-31", 1000.0, form="10-K", filed="2025-01-15", accn="a2"),
    ]

    assert detect_restatements(facts) == []


def test_tier1_fires_on_real_apple_fy2007_amendment_despite_tiny_size(make_edgar_fact):
    # Real Apple FY2007 NetIncomeLoss restatement, confirmed live during Phase
    # 34 verification -- only a 0.03% divergence, but a genuine 10-K/A was
    # filed. Tier 1 fires regardless of size: the amendment itself is the
    # signal, not the dollar amount.
    facts = [
        make_edgar_fact("NetIncomeLoss", "2007-09-29", 3496000000.0, form="10-K",
                         filed="2009-10-27", accn="0001193125-09-214859", start="2006-10-01"),
        make_edgar_fact("NetIncomeLoss", "2007-09-29", 3495000000.0, form="10-K/A",
                         filed="2010-01-25", accn="0001193125-10-012091", start="2006-10-01"),
    ]

    flags = detect_restatements(facts)

    assert len(flags) == 1
    assert flags[0].flag_type == "restatement"
    assert flags[0].severity == "moderate"  # < 5% divergence
    assert "10-K/A" in flags[0].description
    assert flags[0].period == "2007-09-29"


def test_tier1_severity_scales_with_size_real_apple_fy2008_case(make_edgar_fact):
    # Real Apple FY2008 NetIncomeLoss restatement -- lines up with Apple's
    # actual, publicly documented 2009-2010 restatement for stock-option-
    # backdating accounting (SFAS 123R). 26.6% divergence -> "high".
    facts = [
        make_edgar_fact("NetIncomeLoss", "2008-09-27", 4834000000.0, form="10-K",
                         filed="2009-10-27", accn="0001193125-09-214859", start="2007-09-30"),
        make_edgar_fact("NetIncomeLoss", "2008-09-27", 6119000000.0, form="10-K/A",
                         filed="2010-01-25", accn="0001193125-10-012091", start="2007-09-30"),
    ]

    flags = detect_restatements(facts)

    assert len(flags) == 1
    assert flags[0].severity == "high"


def test_tier1_dedupes_against_cascading_echoes_in_later_filings(make_edgar_fact):
    # The same real Apple FY2008 case, but with the corrected value echoed
    # forward as a comparative figure in two more later annual filings --
    # confirmed to happen in the real data. Must produce exactly ONE flag,
    # not one per echo.
    facts = [
        make_edgar_fact("NetIncomeLoss", "2008-09-27", 4834000000.0, form="10-K",
                         filed="2009-10-27", accn="accn1", start="2007-09-30"),
        make_edgar_fact("NetIncomeLoss", "2008-09-27", 6119000000.0, form="10-K/A",
                         filed="2010-01-25", accn="accn2", start="2007-09-30"),
        make_edgar_fact("NetIncomeLoss", "2008-09-27", 6119000000.0, form="10-K",
                         filed="2010-10-27", accn="accn3", start="2007-09-30"),
        make_edgar_fact("NetIncomeLoss", "2008-09-27", 6119000000.0, form="10-K",
                         filed="2011-10-26", accn="accn4", start="2007-09-30"),
    ]

    flags = detect_restatements(facts)

    assert len(flags) == 1


def test_real_jpm_amendment_case(make_edgar_fact):
    # Real JPM 2012 Q1 NetIncomeLoss -- 10-Q/A filed shortly after the
    # original 10-Q. 9.3% divergence.
    facts = [
        make_edgar_fact("NetIncomeLoss", "2012-03-31", 5383000000.0, form="10-Q",
                         filed="2012-05-10", accn="0000019617-12-000213", start="2012-01-01"),
        make_edgar_fact("NetIncomeLoss", "2012-03-31", 4924000000.0, form="10-Q/A",
                         filed="2012-08-09", accn="0000019617-12-000262", start="2012-01-01"),
        make_edgar_fact("NetIncomeLoss", "2012-03-31", 4924000000.0, form="10-Q",
                         filed="2013-05-08", accn="0000019617-13-000300", start="2012-01-01"),
    ]

    flags = detect_restatements(facts)

    assert len(flags) == 1
    assert flags[0].severity == "high"  # ~9.3%, between the 5% and 30% bands


def test_tier2_fires_on_large_drift_with_no_amendment_filing(make_edgar_fact):
    # Modeled on MSFT's real net_income divergence pattern (sustained
    # ~20%+ swings across many quarters in 2015-2018, most likely a tax-law
    # transition adjustment, not fraud) -- no /A filing anywhere, but the
    # size clears the Tier 2 bar, so it's still worth surfacing at lower
    # confidence.
    facts = [
        make_edgar_fact("NetIncomeLoss", "2016-09-30", 4690000000.0, form="10-Q",
                         filed="2016-10-20", accn="a1", start="2016-07-01"),
        make_edgar_fact("NetIncomeLoss", "2016-09-30", 5667000000.0, form="10-Q",
                         filed="2017-10-26", accn="a2", start="2016-07-01"),
    ]

    flags = detect_restatements(facts)

    assert len(flags) == 1
    assert "no formal amendment on record" in flags[0].description
    assert flags[0].severity == "moderate"  # ~20.8%, below the 30% high band


def test_tier2_does_not_fire_just_under_the_threshold(make_edgar_fact):
    facts = [
        make_edgar_fact("Revenues", "2023-12-31", 1000.0, form="10-K", filed="2024-01-15", accn="a1"),
        make_edgar_fact("Revenues", "2023-12-31", 1099.0, form="10-K", filed="2025-01-15", accn="a2"),  # 9.9%
    ]

    assert detect_restatements(facts) == []


def test_rounding_noise_never_flags_real_tsla_style_case(make_edgar_fact):
    # Real TSLA revenue pattern -- later filings round to the nearest
    # million while the original reported exact dollars. ~0.001% divergence.
    facts = [
        make_edgar_fact("Revenues", "2018-12-31", 21461268000.0, form="10-K",
                         filed="2019-02-19", accn="a1", start="2018-01-01"),
        make_edgar_fact("Revenues", "2018-12-31", 21461000000.0, form="10-K",
                         filed="2020-02-13", accn="a2", start="2018-01-01"),
    ]

    assert detect_restatements(facts) == []


def test_different_periods_are_not_grouped_together(make_edgar_fact):
    # Quarterly (3-month) and year-to-date (9-month) figures can share an
    # end date but have different start dates -- the exact grouping bug
    # caught and fixed during Phase 35 scoping. Must not be compared.
    facts = [
        make_edgar_fact("NetIncomeLoss", "2008-06-28", 1072000000.0, form="10-Q",
                         filed="2009-07-22", accn="a1", start="2008-03-30"),
        make_edgar_fact("NetIncomeLoss", "2008-06-28", 3698000000.0, form="10-Q",
                         filed="2009-07-22", accn="a1", start="2007-09-30"),
    ]

    assert detect_restatements(facts) == []
