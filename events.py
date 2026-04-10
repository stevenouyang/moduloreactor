"""
Event system for moduloreactor.

Events are plain dicts with a required "type" key.
The collector accumulates events during a handler's lifecycle
and serialises them into the JSON response.
"""


class EventCollector:
    """Accumulates events emitted during a single request."""

    def __init__(self):
        self._events = []

    def emit(self, event_type, data=None):
        """
        Emit an event.

        Args:
            event_type: str — e.g. "toast", "dom.update", "redirect"
            data: dict — event-specific payload (merged into the event dict)
        """
        event = {"type": event_type}
        if data:
            event.update(data)
        self._events.append(event)

    @property
    def events(self):
        return list(self._events)

    def clear(self):
        self._events.clear()
