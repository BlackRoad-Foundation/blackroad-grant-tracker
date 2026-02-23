"""
BlackRoad Grant Tracker - Grant Application and Funding Tracker
SQLite-backed system for tracking grants from identification through reporting.
"""

import sqlite3
import json
import uuid
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GrantType(str, Enum):
    FEDERAL = "federal"
    STATE = "state"
    PRIVATE = "private"
    FOUNDATION = "foundation"


class GrantStatus(str, Enum):
    IDENTIFIED = "identified"
    APPLYING = "applying"
    SUBMITTED = "submitted"
    AWARDED = "awarded"
    REJECTED = "rejected"
    REPORTING = "reporting"
    CLOSED = "closed"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Grant:
    id: str
    title: str
    funder: str
    amount: float
    type: GrantType
    purpose: str = ""
    deadline: Optional[str] = None
    status: GrantStatus = GrantStatus.IDENTIFIED
    requirements: List[str] = field(default_factory=list)
    reporting_dates: List[str] = field(default_factory=list)
    contacts: List[str] = field(default_factory=list)
    award_amount: Optional[float] = None
    notes: str = ""
    assigned_to: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Submission:
    id: str
    grant_id: str
    submitted_at: str
    notes: str = ""
    submitted_by: str = ""
    documents: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GrantNote:
    id: str
    grant_id: str
    content: str
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class GrantDatabase:
    def __init__(self, db_path: str = "grants.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS grants (
                    id              TEXT PRIMARY KEY,
                    title           TEXT NOT NULL,
                    funder          TEXT NOT NULL,
                    amount          REAL NOT NULL DEFAULT 0,
                    type            TEXT NOT NULL,
                    purpose         TEXT DEFAULT '',
                    deadline        TEXT,
                    status          TEXT DEFAULT 'identified',
                    requirements    TEXT DEFAULT '[]',
                    reporting_dates TEXT DEFAULT '[]',
                    contacts        TEXT DEFAULT '[]',
                    award_amount    REAL,
                    notes           TEXT DEFAULT '',
                    assigned_to     TEXT DEFAULT '',
                    created_at      TEXT NOT NULL,
                    updated_at      TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS submissions (
                    id           TEXT PRIMARY KEY,
                    grant_id     TEXT NOT NULL REFERENCES grants(id),
                    submitted_at TEXT NOT NULL,
                    notes        TEXT DEFAULT '',
                    submitted_by TEXT DEFAULT '',
                    documents    TEXT DEFAULT '[]',
                    created_at   TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS grant_notes (
                    id         TEXT PRIMARY KEY,
                    grant_id   TEXT NOT NULL REFERENCES grants(id),
                    content    TEXT NOT NULL,
                    author     TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_grant_status ON grants(status);
                CREATE INDEX IF NOT EXISTS idx_grant_funder ON grants(funder);
                CREATE INDEX IF NOT EXISTS idx_sub_grant ON submissions(grant_id);
            """)


# ---------------------------------------------------------------------------
# Grant Tracker Service
# ---------------------------------------------------------------------------

class GrantTracker:
    def __init__(self, db_path: str = "grants.db"):
        self.db = GrantDatabase(db_path)
        self.conn = self.db.conn

    # -----------------------------------------------------------------------
    # Grant lifecycle
    # -----------------------------------------------------------------------

    def identify(
        self,
        title: str,
        funder: str,
        amount: float,
        deadline: Optional[str] = None,
        grant_type: GrantType = GrantType.FOUNDATION,
        purpose: str = "",
        requirements: Optional[List[str]] = None,
        contacts: Optional[List[str]] = None,
        assigned_to: str = "",
    ) -> Grant:
        """Add a newly identified grant opportunity."""
        now = datetime.utcnow().isoformat()
        grant = Grant(
            id=str(uuid.uuid4()),
            title=title,
            funder=funder,
            amount=amount,
            type=grant_type,
            purpose=purpose,
            deadline=deadline,
            requirements=requirements or [],
            contacts=contacts or [],
            assigned_to=assigned_to,
            created_at=now,
            updated_at=now,
        )
        with self.conn:
            self.conn.execute(
                """INSERT INTO grants
                   (id, title, funder, amount, type, purpose, deadline, status,
                    requirements, reporting_dates, contacts, award_amount, notes,
                    assigned_to, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (grant.id, grant.title, grant.funder, grant.amount,
                 grant.type.value, grant.purpose, grant.deadline,
                 grant.status.value, json.dumps(grant.requirements),
                 json.dumps(grant.reporting_dates), json.dumps(grant.contacts),
                 grant.award_amount, grant.notes, grant.assigned_to,
                 grant.created_at, grant.updated_at),
            )
        return grant

    def get_grant(self, grant_id: str) -> Optional[Grant]:
        row = self.conn.execute(
            "SELECT * FROM grants WHERE id = ?", (grant_id,)
        ).fetchone()
        return self._row_to_grant(row) if row else None

    def list_grants(
        self,
        status: Optional[GrantStatus] = None,
        grant_type: Optional[GrantType] = None,
        funder: Optional[str] = None,
    ) -> List[Grant]:
        query = "SELECT * FROM grants WHERE 1=1"
        params: List[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status.value)
        if grant_type:
            query += " AND type = ?"
            params.append(grant_type.value)
        if funder:
            query += " AND funder = ?"
            params.append(funder)
        query += " ORDER BY deadline ASC"
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_grant(r) for r in rows]

    def apply(self, grant_id: str, notes: str = "", assigned_to: str = "") -> Optional[Grant]:
        """Move grant to 'applying' status."""
        return self._transition(grant_id, GrantStatus.APPLYING, notes=notes)

    def submit(self, grant_id: str, notes: str = "", submitted_by: str = "",
               documents: Optional[List[str]] = None) -> Optional[Grant]:
        """Record submission and update status."""
        grant = self.get_grant(grant_id)
        if not grant:
            return None
        now = datetime.utcnow().isoformat()
        # Create submission record
        sub = Submission(
            id=str(uuid.uuid4()),
            grant_id=grant_id,
            submitted_at=now,
            notes=notes,
            submitted_by=submitted_by,
            documents=documents or [],
        )
        with self.conn:
            self.conn.execute(
                """INSERT INTO submissions
                   (id, grant_id, submitted_at, notes, submitted_by, documents, created_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (sub.id, sub.grant_id, sub.submitted_at, sub.notes,
                 sub.submitted_by, json.dumps(sub.documents), sub.created_at),
            )
        return self._transition(grant_id, GrantStatus.SUBMITTED)

    def award(
        self,
        grant_id: str,
        award_amount: Optional[float] = None,
        reporting_dates: Optional[List[str]] = None,
    ) -> Optional[Grant]:
        """Mark grant as awarded with optional actual amount."""
        grant = self.get_grant(grant_id)
        if not grant:
            return None
        actual = award_amount if award_amount is not None else grant.amount
        dates_json = json.dumps(reporting_dates or [])
        now = datetime.utcnow().isoformat()
        with self.conn:
            self.conn.execute(
                """UPDATE grants SET status = 'awarded', award_amount = ?,
                   reporting_dates = ?, updated_at = ? WHERE id = ?""",
                (actual, dates_json, now, grant_id),
            )
        return self.get_grant(grant_id)

    def reject(self, grant_id: str, notes: str = "") -> Optional[Grant]:
        """Mark grant as rejected."""
        return self._transition(grant_id, GrantStatus.REJECTED, notes=notes)

    def start_reporting(self, grant_id: str) -> Optional[Grant]:
        return self._transition(grant_id, GrantStatus.REPORTING)

    def close(self, grant_id: str) -> Optional[Grant]:
        return self._transition(grant_id, GrantStatus.CLOSED)

    def _transition(self, grant_id: str, new_status: GrantStatus,
                    notes: str = "") -> Optional[Grant]:
        if not self.get_grant(grant_id):
            return None
        now = datetime.utcnow().isoformat()
        with self.conn:
            self.conn.execute(
                "UPDATE grants SET status = ?, updated_at = ? WHERE id = ?",
                (new_status.value, now, grant_id),
            )
            if notes:
                self.conn.execute(
                    "UPDATE grants SET notes = ? WHERE id = ?", (notes, grant_id)
                )
        return self.get_grant(grant_id)

    def add_note(self, grant_id: str, content: str, author: str = "") -> GrantNote:
        note = GrantNote(id=str(uuid.uuid4()), grant_id=grant_id,
                         content=content, author=author)
        with self.conn:
            self.conn.execute(
                "INSERT INTO grant_notes (id, grant_id, content, author, created_at) VALUES (?,?,?,?,?)",
                (note.id, note.grant_id, note.content, note.author, note.created_at),
            )
        return note

    def get_notes(self, grant_id: str) -> List[GrantNote]:
        rows = self.conn.execute(
            "SELECT * FROM grant_notes WHERE grant_id = ? ORDER BY created_at DESC",
            (grant_id,),
        ).fetchall()
        return [GrantNote(id=r["id"], grant_id=r["grant_id"], content=r["content"],
                          author=r["author"], created_at=r["created_at"])
                for r in rows]

    def get_submissions(self, grant_id: str) -> List[Submission]:
        rows = self.conn.execute(
            "SELECT * FROM submissions WHERE grant_id = ? ORDER BY submitted_at DESC",
            (grant_id,),
        ).fetchall()
        return [Submission(id=r["id"], grant_id=r["grant_id"], submitted_at=r["submitted_at"],
                           notes=r["notes"], submitted_by=r["submitted_by"],
                           documents=json.loads(r["documents"]), created_at=r["created_at"])
                for r in rows]

    # -----------------------------------------------------------------------
    # Analytics
    # -----------------------------------------------------------------------

    def get_pipeline(self) -> Dict[str, Any]:
        """Full grant pipeline summary by status."""
        rows = self.conn.execute(
            """SELECT status, COUNT(*) as count, SUM(amount) as requested,
               SUM(CASE WHEN award_amount IS NOT NULL THEN award_amount ELSE 0 END) as awarded
               FROM grants GROUP BY status"""
        ).fetchall()
        pipeline = {}
        total_requested = 0.0
        total_awarded = 0.0
        for r in rows:
            pipeline[r["status"]] = {
                "count": r["count"],
                "total_requested": round(r["requested"] or 0, 2),
                "total_awarded": round(r["awarded"] or 0, 2),
            }
            total_requested += r["requested"] or 0
            total_awarded += r["awarded"] or 0
        return {
            "by_status": pipeline,
            "total_grants": sum(v["count"] for v in pipeline.values()),
            "total_requested": round(total_requested, 2),
            "total_awarded": round(total_awarded, 2),
        }

    def reporting_calendar(self, months: int = 3) -> List[Dict[str, Any]]:
        """Return upcoming reporting obligations within the next N months."""
        today = date.today()
        cutoff = (today + timedelta(days=months * 30)).isoformat()
        grants = self.list_grants(status=GrantStatus.REPORTING)
        upcoming = []
        for g in grants:
            for rd in g.reporting_dates:
                if today.isoformat() <= rd <= cutoff:
                    upcoming.append({
                        "grant_id": g.id,
                        "title": g.title,
                        "funder": g.funder,
                        "reporting_date": rd,
                        "award_amount": g.award_amount,
                    })
        upcoming.sort(key=lambda x: x["reporting_date"])
        return upcoming

    def success_rate(self, funder_filter: Optional[str] = None) -> Dict[str, Any]:
        """Win rate: awarded / (submitted + awarded + rejected)."""
        query = "SELECT status, COUNT(*) FROM grants WHERE status IN ('submitted','awarded','rejected')"
        params: List[Any] = []
        if funder_filter:
            query += " AND funder = ?"
            params.append(funder_filter)
        query += " GROUP BY status"
        rows = self.conn.execute(query, params).fetchall()
        counts = {r[0]: r[1] for r in rows}
        awarded = counts.get("awarded", 0)
        rejected = counts.get("rejected", 0)
        submitted = counts.get("submitted", 0)
        total_decided = awarded + rejected
        return {
            "funder": funder_filter or "all",
            "submitted": submitted,
            "awarded": awarded,
            "rejected": rejected,
            "success_rate": round(awarded / total_decided, 3) if total_decided else 0,
        }

    def upcoming_deadlines(self, days: int = 30) -> List[Grant]:
        """Grants with deadlines within the next N days."""
        today = date.today().isoformat()
        cutoff = (date.today() + timedelta(days=days)).isoformat()
        rows = self.conn.execute(
            """SELECT * FROM grants WHERE deadline BETWEEN ? AND ?
               AND status IN ('identified','applying')
               ORDER BY deadline ASC""",
            (today, cutoff),
        ).fetchall()
        return [self._row_to_grant(r) for r in rows]

    def total_funding_by_type(self) -> Dict[str, float]:
        rows = self.conn.execute(
            "SELECT type, SUM(award_amount) as total FROM grants WHERE status='awarded' GROUP BY type"
        ).fetchall()
        return {r["type"]: round(r["total"] or 0, 2) for r in rows}

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _row_to_grant(self, row: sqlite3.Row) -> Grant:
        return Grant(
            id=row["id"], title=row["title"], funder=row["funder"],
            amount=row["amount"], type=GrantType(row["type"]),
            purpose=row["purpose"], deadline=row["deadline"],
            status=GrantStatus(row["status"]),
            requirements=json.loads(row["requirements"]),
            reporting_dates=json.loads(row["reporting_dates"]),
            contacts=json.loads(row["contacts"]),
            award_amount=row["award_amount"], notes=row["notes"],
            assigned_to=row["assigned_to"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def close_db(self) -> None:
        self.conn.close()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo() -> None:
    import tempfile, os
    db_file = tempfile.mktemp(suffix=".db")
    gt = GrantTracker(db_file)

    print("\n=== Identifying Grants ===")
    g1 = gt.identify("NSF Community Tech Grant", "NSF", 250_000,
                     deadline="2025-04-30", grant_type=GrantType.FEDERAL,
                     requirements=["IRS 501c3", "Budget narrative"])
    g2 = gt.identify("Gates Foundation Tech", "Gates Foundation", 500_000,
                     deadline="2025-06-15", grant_type=GrantType.FOUNDATION)
    g3 = gt.identify("State Innovation Fund", "State of Texas", 75_000,
                     deadline="2025-03-01", grant_type=GrantType.STATE)
    print(f"  Identified: {g1.title}, {g2.title}, {g3.title}")

    print("\n=== Moving Through Pipeline ===")
    gt.apply(g1.id, notes="Started application")
    gt.submit(g1.id, submitted_by="Alice Chen", documents=["budget.pdf", "narrative.pdf"])
    gt.award(g1.id, award_amount=200_000, reporting_dates=["2025-12-31", "2026-06-30"])
    gt.start_reporting(g1.id)

    gt.apply(g2.id)
    gt.reject(g3.id, notes="Missed deadline")
    print("  G1: identified→applying→submitted→awarded→reporting")
    print("  G2: identified→applying")
    print("  G3: identified→rejected")

    print("\n=== Pipeline Summary ===")
    pipeline = gt.get_pipeline()
    print(f"  Total grants: {pipeline['total_grants']}")
    print(f"  Total requested: ${pipeline['total_requested']:,.2f}")
    print(f"  Total awarded:   ${pipeline['total_awarded']:,.2f}")
    for status, data in pipeline["by_status"].items():
        print(f"    {status}: {data['count']} grants")

    print("\n=== Success Rate ===")
    sr = gt.success_rate()
    print(f"  Win rate: {sr['success_rate']:.1%} ({sr['awarded']} awarded / {sr['awarded']+sr['rejected']} decided)")

    gt.close_db()
    os.unlink(db_file)
    print("\n✓ Demo complete")


if __name__ == "__main__":
    demo()
