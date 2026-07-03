from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class StudentSummary:
    uuid: str
    name: str
    location: str
    rate: int
    last_payment_date: Optional[str]
    attendance_percentage: float
    meeting_times_summary: str
    status: str

@dataclass
class MeetingTime:
    day: str
    time: str
    type: str
    is_in_person: bool
    meeting_id: Optional[str] = None

@dataclass
class Relationship:
    other_uuid: str
    relationship_type: str
    invoice_group: bool = False

@dataclass
class StudentProfile:
    uuid: str
    name: str
    location: str
    timezone: str
    age_group: str
    academic_year: str
    telegram: str
    is_minor: bool
    parent_name: str
    school_name: str
    educational_goals: str
    behavioral_comments: str
    general_comments: str
    rate: int
    phones: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    parent_phones: List[str] = field(default_factory=list)
    parent_emails: List[str] = field(default_factory=list)
    meeting_times: List[MeetingTime] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)

@dataclass
class AttendanceRecord:
    id: Optional[int] = None
    meeting_id: Optional[str] = None
    date: str = ''
    status: str = 'absent'

@dataclass
class PaymentRecord:
    id: Optional[int] = None
    date: str = ''
    amount: int = 0
    receipt_image: Optional[bytes] = None

@dataclass
class ActionItem:
    id: Optional[int] = None
    text: str = ''
    done: bool = False
    created: str = ''