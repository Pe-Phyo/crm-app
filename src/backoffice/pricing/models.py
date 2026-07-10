from dataclasses import dataclass
from typing import Optional

@dataclass
class PackageTemplate:
    teacher_id: str
    name: str
    type: str              # 'private' or 'group'
    lesson_count: int
    default_rate: int      # MMK
    subject: str = ''
    billing_cycle: str = 'monthly'
    schedule_json: str = '[]'  # JSON string of [{"day":"Monday","time":"09:00"},...]
    id: Optional[int] = None   # set after insert