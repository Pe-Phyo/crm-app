from . import base
from . import teacher

ROLE_SCHEMAS = {
    'admin': base.SCHEMA,
    'front_office': base.SCHEMA,
    'back_office': base.SCHEMA,
    'bot': base.SCHEMA,
    'teacher': teacher.SCHEMA,
    'contractor': base.SCHEMA,
}
