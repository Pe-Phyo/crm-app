from typing import Any, Tuple
from ..staff import auth as staff_auth

from .widgets.summary import get_summary
from .widgets.inbox.config import get_inbox_config
from .widgets.inbox.handler import get_inbox_items, create_note, update_inbox_item
from .widgets.analytics.handler import get_analytics
from .widgets.build_status.handler import get_build_status
from .widgets.upcoming_events.handler import get_upcoming_events


class DashboardCoordinator:
    def handle(self, method: str, path: str, body: str = None, headers: dict = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        session = staff_auth.verify_session(token)
        if not session:
            return {'error': 'Unauthorized'}, 401

        role = session['role']

        if method == 'GET':
            if path == '/dashboard/summary':
                return get_summary(role), 200
            if path.startswith('/dashboard/inbox-config'):
                return get_inbox_config(role), 200
            if path == '/dashboard/inbox':
                return get_inbox_items(role), 200
            if path.startswith('/dashboard/analytics/'):
                chart_id = path.split('/')[-1]
                return get_analytics(chart_id, role), 200
            if path == '/dashboard/build-status':
                return get_build_status(), 200
            if path.startswith('/dashboard/upcoming-events'):
                days = 14
            if path.startswith('/dashboard/upcoming-events'):
                days = 14
                if '?days=' in path:
                    try:
                        days = int(path.split('?days=')[1].split('&')[0])
                    except:
                        pass
                return get_upcoming_events(days), 200

        elif method == 'POST':
            if path == '/dashboard/inbox/note':
                return create_note(session, body), 201

        elif method == 'PATCH':
            if path.startswith('/dashboard/inbox/'):
                item_id = int(path.split('/')[-1])
                return update_inbox_item(item_id, body), 200

        return {'error': 'Not found'}, 404