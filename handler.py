import json
from functools import wraps

from django.http import HttpResponseNotAllowed, JsonResponse

from .debug import log_action
from .events import EventCollector
from .orchestrator_bridge import render_components


class HtmxHandler:
    """
    Request handler injected by @htmx_action.

    Provides:
        - Session read/write
        - Event emission (toast, alert, dom.update, redirect, custom)
        - Optional orchestrator bridge for component rendering
    """

    def __init__(self, request):
        self.request = request
        self.POST = request.POST
        self.GET = request.GET
        self._collector = EventCollector()
        self._session_ops = []

    # ── Session ─────────────────────────────────────────────

    def get_session(self, key, default=None):
        return self.request.session.get(key, default)

    def set_session(self, key, value):
        self.request.session[key] = value
        self.request.session.modified = True
        self._session_ops.append({"op": "set", "key": key})

    def del_session(self, key):
        self.request.session.pop(key, None)
        self.request.session.modified = True
        self._session_ops.append({"op": "del", "key": key})

    # ── Events (generic) ───────────────────────────────────

    def emit(self, event_type, data=None):
        """Emit any event. Primary API."""
        self._collector.emit(event_type, data)

    # ── Event shortcuts ────────────────────────────────────

    def toast(self, message, level="info"):
        self.emit("toast", {"message": message, "level": level})

    def alert(self, message, level="info", dismissible=True):
        self.emit("alert", {
            "message": message,
            "level": level,
            "dismissible": dismissible,
        })

    def dom_update(self, target, html, swap="outerHTML"):
        self.emit("dom.update", {
            "target": target,
            "html": html,
            "swap": swap,
        })

    def dom_remove(self, target):
        self.emit("dom.remove", {"target": target})

    def redirect(self, url):
        self.emit("redirect", {"url": url})

    # ── Orchestrator bridge (optional) ─────────────────────

    def render_components(self, component_ids):
        """
        Render components via the project orchestrator and emit
        dom.update events for each rendered fragment.

        Requires MODULOREACTOR["ORCHESTRATOR"] in settings.
        """
        client_hashes = json.loads(
            self.request.headers.get("X-Component-Hashes", "{}")
        )
        rendered = render_components(
            self.request, component_ids, client_hashes
        )
        for cid, html in rendered.items():
            self.dom_update(f"#{cid}", html)

    # ── Response builder ───────────────────────────────────

    def _build_response(self):
        return JsonResponse({"events": self._collector.events})


# ── Decorator ───────────────────────────────────────────────


def htmx_action(require_post=True):
    """
    Decorator that wraps a view into the event-driven HTMX lifecycle.

    Usage:
        @htmx_action()
        def my_action(h):
            h.set_session("key", "value")
            h.toast("Done!", "success")
            h.dom_update("#target", "<div id='target'>new</div>")
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(request, *args, **kwargs):
            if require_post and request.method != "POST":
                return HttpResponseNotAllowed(["POST"])
            h = HtmxHandler(request)
            fn(h, *args, **kwargs)
            log_action(fn.__name__, h._collector.events, h._session_ops)
            return h._build_response()

        return wrapper

    return decorator
