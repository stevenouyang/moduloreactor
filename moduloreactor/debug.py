import json
import logging

from django.conf import settings

logger = logging.getLogger("moduloreactor")


def _cfg():
    return getattr(settings, "MODULOREACTOR", {})


def is_debug():
    return _cfg().get("DEBUG", False)


def log_action(action_name, events, session_ops):
    """Log a completed action's lifecycle to the moduloreactor logger."""
    if not is_debug():
        return
    logger.debug(
        "[moduloreactor:action] %s",
        json.dumps(
            {
                "action": action_name,
                "events_emitted": [
                    {"type": e.get("type")} for e in events
                ],
                "session_mutations": session_ops,
            },
            indent=2,
            default=str,
        ),
    )
