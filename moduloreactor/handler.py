import json
from functools import wraps

from django.http import HttpResponseNotAllowed, JsonResponse

from .debug import log_action
from .events import EventCollector
from .orchestrator_bridge import render_components

# Session key for next-request message queue
_NEXT_KEY = "_mr_next_messages"


class HtmxHandler:
    """
    Request handler injected by @htmx_action.

    Provides:
        - Session read/write
        - Event emission (toast, alert, confirm, choice, dom.update, dom.append, dom.remove, redirect)
        - Next-request message queue (survives redirects)
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

    # ── Messages ───────────────────────────────────────────
    #
    # toast / alert / confirm / choice — unified message pipeline.
    # All messages go through the same event system.
    # Use `next=True` to queue messages for after a redirect.
    #

    def toast(self, message, level="info", duration=3000, next=False):
        event = {"message": message, "level": level, "duration": duration}
        if next:
            self._queue_next("toast", event)
        else:
            self.emit("toast", event)

    def alert(self, message, level="info", dismissible=True, next=False):
        event = {"message": message, "level": level, "dismissible": dismissible}
        if next:
            self._queue_next("alert", event)
        else:
            self.emit("alert", event)

    def confirm(self, message, on_confirm, payload=None, on_cancel=None,
                title=None, confirm_label="Confirm", cancel_label="Cancel",
                style="default"):
        """
        Show a confirm dialog. When user confirms, fires `on_confirm`
        as an HTMX POST with the given payload.

        Args:
            message:       Dialog message text
            on_confirm:    URL to POST when confirmed
            payload:       dict of data to send with the confirm POST
            on_cancel:     URL to POST when cancelled (optional)
            title:         Optional dialog title
            confirm_label: Text for confirm button (default "Confirm")
            cancel_label:  Text for cancel button (default "Cancel")
            style:         "default" or "danger" — affects confirm button color
        """
        self.emit("confirm", {
            "message": message,
            "title": title,
            "on_confirm": on_confirm,
            "on_cancel": on_cancel,
            "payload": payload or {},
            "confirm_label": confirm_label,
            "cancel_label": cancel_label,
            "style": style,
        })

    def choice(self, message, options, title=None):
        """
        Show a choice dialog with multiple action buttons.

        Args:
            message: Dialog message text
            title:   Optional dialog title
            options: List of dicts, each with:
                     - label: Button text
                     - url:   URL to POST when selected
                     - payload: dict (optional)
                     - style: "default" | "danger" | "secondary" (optional)
        """
        self.emit("choice", {
            "message": message,
            "title": title,
            "options": options,
        })

    # ── DOM ─────────────────────────────────────────────────

    def dom_update(self, target, html, swap="outerHTML", many=False):
        """
        Update DOM nodes matching ``target`` (CSS selector).

        Args:
            target: CSS selector string.
            html:   HTML fragment to apply.
            swap:   ``outerHTML`` (default), ``innerHTML``, ``beforeend``, ``afterbegin``.
            many:   If False (default), only the first match is updated (legacy behavior).
                    If True, every matching element is updated.
        """
        payload = {
            "target": target,
            "html": html,
            "swap": swap,
        }
        if many:
            payload["many"] = True
        self.emit("dom.update", payload)

    def dom_append(self, target, html, many=False):
        """Append HTML inside ``target`` (``dom.update`` with ``swap="beforeend"``)."""
        self.dom_update(target, html, swap="beforeend", many=many)

    def dom_remove(self, target, many=False):
        """
        Remove DOM nodes matching ``target`` (CSS selector).

        Args:
            target: CSS selector string.
            many:   If False (default), only the first match is removed.
                    If True, every matching element is removed.
        """
        payload = {"target": target}
        if many:
            payload["many"] = True
        self.emit("dom.remove", payload)

    def redirect(self, url):
        self.emit("redirect", {"url": url})

    # ── Next-request queue ──────────────────────────────────

    def _queue_next(self, event_type, data):
        """Store a message in session to be delivered on the next page load."""
        queue = self.request.session.get(_NEXT_KEY, [])
        event = {"type": event_type}
        event.update(data)
        queue.append(event)
        self.request.session[_NEXT_KEY] = queue
        self.request.session.modified = True

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


def drain_next_messages(request):
    """
    Pop queued next-request messages from session.
    Call this in template tags or views to get messages stored by
    h.toast("...", next=True) or h.alert("...", next=True).
    Returns a list of event dicts.
    """
    messages = request.session.pop(_NEXT_KEY, [])
    if messages:
        request.session.modified = True
    return messages


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
            h.dom_update(".chip", "<span class='chip'>x</span>", swap="innerHTML", many=True)
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
