from urllib.parse import parse_qs
from typing import Optional

ALLOWED_VIEW_AS = {'teacher', 'front_office', 'back_office', 'bot', 'dev'}


def get_effective_role(session: dict, query_string: Optional[str]) -> str:
    """
    Return the role that the dashboard should render.

    - If the user is admin and provides ?view_as=<role> with a valid role,
      return that role (preview mode).
    - Otherwise, return the session's own role.

    Non‑admin users can never impersonate another role.
    """
    role = session.get('role', 'teacher')

    if role != 'admin':
        return role

    if not query_string:
        return role

    params = parse_qs(query_string)
    view_as = params.get('view_as', [None])[0]

    if view_as and view_as in ALLOWED_VIEW_AS:
        return view_as

    return role