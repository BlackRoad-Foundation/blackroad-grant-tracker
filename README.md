# BlackRoad Grant Tracker

> Grant application and funding tracker — SQLite-backed, zero-dependency Python.

## Features

- **Grant Lifecycle** — identified → applying → submitted → awarded/rejected → reporting → closed
- **Submissions** — track submission records, documents, submitters
- **Reporting Calendar** — upcoming reporting obligations
- **Pipeline Analytics** — status breakdown, success rate by funder
- **Deadline Tracking** — upcoming grant deadlines

## Quick Start

```python
from grant_tracker import GrantTracker, GrantType

gt = GrantTracker("grants.db")

grant = gt.identify("NSF Community Grant", "NSF", 250_000,
                    deadline="2025-04-30", grant_type=GrantType.FEDERAL,
                    requirements=["501c3", "Budget narrative"])

gt.apply(grant.id)
gt.submit(grant.id, submitted_by="Alice Chen",
          documents=["budget.pdf", "narrative.pdf"])
gt.award(grant.id, award_amount=200_000,
         reporting_dates=["2025-12-31", "2026-06-30"])

print(gt.get_pipeline())
print(gt.success_rate())
print(gt.reporting_calendar(months=3))
```

## Running Tests

```bash
pip install pytest
pytest test_grant_tracker.py -v
```
