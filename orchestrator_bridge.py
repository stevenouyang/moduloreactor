"""
Bridge to project-specific Orchestrator.

The package NEVER imports the orchestrator directly.
It loads the class path from settings at runtime:

    MODULOREACTOR = {
        "ORCHESTRATOR": "z_fe_boil.orchestrator.Orchestrator",
    }
"""
import json

from django.conf import settings
from django.utils.module_loading import import_string

_orchestrator_cls = None


def get_orchestrator_class():
    """Lazy-load and cache the Orchestrator class from settings."""
    global _orchestrator_cls
    if _orchestrator_cls is None:
        config = getattr(settings, "MODULOREACTOR", {})
        path = config.get("ORCHESTRATOR")
        if path:
            _orchestrator_cls = import_string(path)
    return _orchestrator_cls


def render_components(request, component_ids, client_hashes=None):
    """
    Render components via the configured orchestrator.

    Returns:
        dict  {component_id: raw_html}   (no OOB attributes)
    """
    cls = get_orchestrator_class()
    if not cls:
        return {}
    orch = cls(
        request,
        component_ids=component_ids,
        client_hashes=client_hashes or {},
    )
    orch.execute()
    return dict(orch.rendered)
