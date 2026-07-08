import importlib
import json
from typing import Any, Tuple
from ..staff import auth as staff_auth
from .auth import get_effective_role

# Role‑independent widgets stay here
from .widgets.build_status.handler import get_build_status
from .widgets.upcoming_events.handler import get_upcoming_events


class DashboardCoordinator:
    def handle(self, method: str, path: str, body: str = None,
               headers: dict = None, query: str = None) -> Tuple[Any, int]:
        token = (headers or {}).get('Authorization', '').replace('Bearer ', '')
        session = staff_auth.verify_session(token)
        if not session:
            return {'error': 'Unauthorized'}, 401

        effective_role = get_effective_role(session, query)

        if method == 'GET':
            # --- Summary ---
            if path == '/dashboard/summary':
                mod = self._load_role_widget(effective_role, 'summary')
                return mod.get_summary(), 200

            # --- Inbox config ---
            elif path == '/dashboard/inbox-config':
                mod = self._load_role_widget(effective_role, 'inbox')
                # optional: per‑role heuristics config
                if hasattr(mod, 'get_config'):
                    return mod.get_config(), 200
                return {}, 200

            # --- Inbox items ---
            elif path == '/dashboard/inbox':
                mod = self._load_role_widget(effective_role, 'inbox')
                return mod.get_items(), 200

            # --- Analytics ---
            elif path.startswith('/dashboard/analytics/'):
                chart_id = path.split('/')[-1]
                mod = self._load_role_widget(effective_role, 'analytics')
                return mod.get_chart(chart_id), 200

            # --- Role‑independent ---
            elif path == '/dashboard/build-status':
                return get_build_status(), 200

            elif path.startswith('/dashboard/upcoming-events'):
                days = 14
                if '?days=' in path:
                    try:
                        days = int(path.split('?days=')[1].split('&')[0])
                    except:
                        pass
                return get_upcoming_events(days), 200

        elif method == 'POST':
            if path == '/dashboard/inbox/note':
                mod = self._load_role_widget(effective_role, 'inbox')
                return mod.create_note(session, body), 201

        elif method == 'PATCH':
            if path.startswith('/dashboard/inbox/'):
                item_id = int(path.split('/')[-1])
                mod = self._load_role_widget(effective_role, 'inbox')
                return mod.update_item(item_id, body), 200

        return {'error': 'Not found'}, 404

    def _load_role_widget(self, role: str, widget_name: str):
        """
        Dynamically import src.staff.<role>.widgets.<widget_name>.
        """
        module_path = f'..staff.{role}.widgets.{widget_name}'
        return importlib.import_module(module_path, package=__package__)