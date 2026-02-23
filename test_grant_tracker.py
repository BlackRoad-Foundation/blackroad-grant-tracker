"""pytest tests for BlackRoad Grant Tracker"""
import pytest
from grant_tracker import GrantTracker, GrantType, GrantStatus


@pytest.fixture
def gt(tmp_path):
    g = GrantTracker(str(tmp_path / "test.db"))
    yield g
    g.close_db()


def test_identify_grant(gt):
    g = gt.identify("Test Grant", "NSF", 100_000, grant_type=GrantType.FEDERAL)
    assert g.id
    assert g.status == GrantStatus.IDENTIFIED

def test_apply(gt):
    g = gt.identify("Grant", "Funder", 50_000)
    applied = gt.apply(g.id)
    assert applied.status == GrantStatus.APPLYING

def test_submit(gt):
    g = gt.identify("Grant", "Funder", 50_000)
    gt.apply(g.id)
    submitted = gt.submit(g.id, submitted_by="Alice")
    assert submitted.status == GrantStatus.SUBMITTED
    subs = gt.get_submissions(g.id)
    assert len(subs) == 1

def test_award(gt):
    g = gt.identify("Grant", "Funder", 50_000)
    gt.submit(g.id)
    awarded = gt.award(g.id, award_amount=45_000,
                       reporting_dates=["2025-12-31"])
    assert awarded.status == GrantStatus.AWARDED
    assert awarded.award_amount == 45_000
    assert len(awarded.reporting_dates) == 1

def test_reject(gt):
    g = gt.identify("Grant", "Funder", 50_000)
    rejected = gt.reject(g.id)
    assert rejected.status == GrantStatus.REJECTED

def test_get_pipeline(gt):
    g1 = gt.identify("G1", "F1", 100_000)
    g2 = gt.identify("G2", "F1", 200_000)
    gt.award(g1.id, award_amount=90_000)
    pipeline = gt.get_pipeline()
    assert pipeline["total_grants"] == 2
    assert pipeline["total_requested"] == 300_000

def test_success_rate(gt):
    g1 = gt.identify("G1", "NSF", 100_000)
    g2 = gt.identify("G2", "NSF", 50_000)
    gt.award(g1.id)
    gt.reject(g2.id)
    sr = gt.success_rate()
    assert sr["awarded"] == 1
    assert sr["rejected"] == 1
    assert sr["success_rate"] == 0.5

def test_list_by_status(gt):
    gt.identify("G1", "F1", 100_000)
    g2 = gt.identify("G2", "F2", 50_000)
    gt.award(g2.id)
    awarded = gt.list_grants(status=GrantStatus.AWARDED)
    assert len(awarded) == 1

def test_add_note(gt):
    g = gt.identify("G", "F", 10_000)
    note = gt.add_note(g.id, "Important note", author="Alice")
    notes = gt.get_notes(g.id)
    assert len(notes) == 1
    assert notes[0].content == "Important note"

def test_upcoming_deadlines(gt):
    from datetime import date, timedelta
    soon = (date.today() + timedelta(days=7)).isoformat()
    gt.identify("Soon Grant", "F", 10_000, deadline=soon)
    deadlines = gt.upcoming_deadlines(days=30)
    assert len(deadlines) >= 1
