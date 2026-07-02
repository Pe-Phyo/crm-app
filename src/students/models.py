from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class StudentSummary:
    """Non-sensitive fields for the student list panel."""
    uuid: str
    name: str
    location: str
    rate: int
    last_payment_date: Optional[str]   # ISO date string
    attendance_percentage: float
    meeting_times_summary: str          # e.g., "Mon 9am (Group), Wed 3pm (Private)"
    status: str                         # 'active' or 'inactive'

@dataclass
class MeetingTime:
    """A single meeting slot belonging to a student (custom or linked)."""
    day: str
    time: str
    type: str               # 'private' or 'group'
    is_in_person: bool
    meeting_id: Optional[str] = None   # if linked to an existing meeting

@dataclass
class StudentProfile:
    """All fields stored in the per‑student encrypted DB."""
    uuid: str
    name: str
    location: str
    timezone: str
    age_group: str
    academic_year: str
    phone: str
    telegram: str
    email: str
    is_minor: bool
    parent_name: str
    parent_phone: str
    educational_goals: str
    behavioral_comments: str
    general_comments: str
    meeting_times: List[MeetingTime] = field(default_factory=list)

@dataclass
class AttendanceRecord:
    """A single attendance log entry."""
    id: Optional[int] = None           # assigned by DB
    meeting_id: Optional[str] = None
    date: str = ''                     # YYYY-MM-DD
    status: str = 'absent'             # present / absent / late

@dataclass
class PaymentRecord:
    """A single payment record."""
    id: Optional[int] = None
    date: str = ''
    amount: int = 0
    receipt_image: Optional[bytes] = None   # BLOB from DB

@dataclass
class ActionItem:
    """Global to‑do item."""
    id: Optional[int] = None
    text: str = ''
    done: bool = False
    created: str = ''                  # ISO datetime