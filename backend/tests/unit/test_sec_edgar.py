from app.services.sec_edgar import extract_concept_history


def make_companyfacts(concept_units: dict[str, dict]) -> dict:
    """Builds a minimal companyfacts-shaped dict: {concept: {"USD": [entries]}}
    for each concept, matching the real data.sec.gov/api/xbrl/companyfacts
    shape this function actually parses."""
    return {
        "facts": {
            "us-gaap": {
                concept: {"units": units}
                for concept, units in concept_units.items()
            }
        }
    }


# Real Apple FY2007 NetIncomeLoss restatement, as confirmed live during Phase
# 34 verification (MASTER_IMPLEMENTATION_PLAN.md) -- same period, two filings,
# two different values.
APPLE_FY2007_NET_INCOME_RESTATEMENT = [
    {
        "start": "2006-10-01", "end": "2007-09-29", "val": 3496000000,
        "accn": "0001193125-09-214859", "form": "10-K", "filed": "2009-10-27",
    },
    {
        "start": "2006-10-01", "end": "2007-09-29", "val": 3495000000,
        "accn": "0001193125-10-012091", "form": "10-K/A", "filed": "2010-01-25",
    },
]


def test_no_facts_at_all_returns_empty_list():
    result = extract_concept_history({}, ["NetIncomeLoss"])

    assert result == []


def test_no_matching_candidate_returns_empty_list():
    facts = make_companyfacts({"Assets": {"USD": [{"end": "2023-12-31", "val": 1.0, "accn": "x", "form": "10-K", "filed": "2024-01-01"}]}})

    result = extract_concept_history(facts, ["Revenues", "NetIncomeLoss"])

    assert result == []


def test_skips_absent_candidates_and_returns_the_present_one():
    facts = make_companyfacts({
        "NetIncomeLoss": {"USD": APPLE_FY2007_NET_INCOME_RESTATEMENT},
    })

    # "Revenues" isn't present at all -- must still surface "NetIncomeLoss"
    # rather than stopping (or erroring) on the first candidate.
    result = extract_concept_history(facts, ["Revenues", "NetIncomeLoss"])

    assert result == APPLE_FY2007_NET_INCOME_RESTATEMENT


def test_merges_entries_across_every_candidate_with_data_not_just_the_first():
    """Phase 42: a company's tag for the same figure can change era (real
    MSFT data -- "Revenues" covers 2009-2010, "RevenueFromContractWith..."
    covers 2021-2025). Both candidates' entries must come back merged, not
    just whichever candidate happens to be checked first."""
    old_era = [{"start": "2008-07-01", "end": "2009-06-30", "val": 100.0, "accn": "old1", "form": "10-K", "filed": "2009-08-01"}]
    new_era = [{"start": "2024-07-01", "end": "2025-06-30", "val": 500.0, "accn": "new1", "form": "10-K", "filed": "2025-08-01"}]
    facts = make_companyfacts({
        "Revenues": {"USD": old_era},
        "RevenueFromContractWithCustomerExcludingAssessedTax": {"USD": new_era},
    })

    result = extract_concept_history(facts, ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"])

    assert len(result) == 2
    ends = {e["end"] for e in result}
    assert ends == {"2009-06-30", "2025-06-30"}


def test_concept_present_with_no_usd_units_falls_through_to_next_candidate():
    facts = make_companyfacts({
        "Revenues": {"EUR": [{"end": "2023-12-31", "val": 1.0, "accn": "x", "form": "10-K", "filed": "2024-01-01"}]},
        "SalesRevenueNet": {"USD": [{"end": "2023-12-31", "val": 500.0, "accn": "y", "form": "10-K", "filed": "2024-01-01"}]},
    })

    result = extract_concept_history(facts, ["Revenues", "SalesRevenueNet"])

    assert result == facts["facts"]["us-gaap"]["SalesRevenueNet"]["units"]["USD"]


def test_returns_full_restatement_history_not_just_latest():
    """The whole point of this function: a later, amended filing for the same
    period must not silently replace or hide the original value. Both must
    come back, not just the most recent one."""
    facts = make_companyfacts({
        "NetIncomeLoss": {"USD": APPLE_FY2007_NET_INCOME_RESTATEMENT},
    })

    result = extract_concept_history(facts, ["NetIncomeLoss"])

    assert len(result) == 2
    same_period = [e for e in result if e["end"] == "2007-09-29" and e["start"] == "2006-10-01"]
    assert len(same_period) == 2
    values = {e["val"] for e in same_period}
    assert values == {3496000000, 3495000000}
    forms = {e["form"] for e in same_period}
    assert forms == {"10-K", "10-K/A"}
