from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AvailabilitySlot:
    id: Optional[int] = None
    day_of_week: int = 0        # 0=Monday … 6=Sunday
    start_time: str = "09:00"   # HH:MM
    end_time: str = "17:00"
    status: str = "pending"     # pending, approved, rejected

@dataclass
class Holiday:
    id: Optional[int] = None
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    status: str = "pending"

@dataclass
class StaffProfile:
    uuid: str
    username: str
    full_name: str
    display_name: str
    email: str
    phone: str
    timezone: str
    default_hourly_rate: int
    default_meeting_link_pattern: str
    bio: str
    role: str                   # admin, teacher, front_office, back_office, bot
    is_active: bool = False     # only active after admin approval
    password_hash: bytes = b""
    password_salt: bytes = b""
    password_last_changed: str = ""
    must_change_password: bool = False
    payout_taxes_json: str = "" # JSON string for taxes/payout info
    payment_methods_json: str = ""
    created_at: str = ""
    updated_at: str = ""