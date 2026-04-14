import json

from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from moduloreactor.ui_defaults import resolve_ui_template_paths

register = template.Library()


def _get_config():
    return getattr(settings, "MODULOREACTOR", {})


def _render_ui_template_fragments(config):
    """HTML <template> blocks for toast / alert / modal (override paths in settings)."""
    paths = resolve_ui_template_paths(config)
    parts = []
    for key in ("toast", "alert", "modal"):
        parts.append(render_to_string(paths[key], {}))
    return "\n".join(parts)


@register.simple_tag(takes_context=True)
def frontboil(context, debug=None, log_unhandled=None):
    """
    Auto-inject FrontBoil CSS, UI <template> fragments (toast / alert / modal),
    HTMX + frontboil.js + init (next-message queue, hashes, debug).

    Override UI fragments: MODULOREACTOR["UI_TEMPLATES"] — see docs/messages-ui.md.

    Usage:
        {% load moduloreactor %}
        {% frontboil %}
        {% frontboil debug=True %}
    """
    config = _get_config()
    if debug is None:
        debug = config.get("DEBUG", False)
    if log_unhandled is None:
        log_unhandled = config.get("LOG_UNHANDLED_EVENTS", False)

    htmx_url = static("moduloreactor/htmx.min.js")
    fb_js = static("moduloreactor/frontboil.js")
    fb_css = static("moduloreactor/frontboil.css")

    hashes_json = context.get("component_hashes", "{}")

    # Build init options
    opts = {}
    if debug:
        opts["debug"] = True
    if log_unhandled:
        opts["logUnhandled"] = True

    # Drain next-request messages from session
    request = context.get("request")
    if request:
        from moduloreactor.handler import drain_next_messages
        next_msgs = drain_next_messages(request)
        if next_msgs:
            opts["nextMessages"] = next_msgs

    # Merge hashes
    if hashes_json and hashes_json != "{}":
        opts_json = json.dumps(opts)
        opts_json = opts_json[:-1] + (', ' if opts else '') + '"hashes": ' + hashes_json + "}"
    else:
        opts_json = json.dumps(opts)

    ui_fragments = _render_ui_template_fragments(config)
    lines = [
        f'<link rel="stylesheet" href="{fb_css}">',
        ui_fragments,
        f'<script src="{htmx_url}"></script>',
        f'<script src="{fb_js}"></script>',
        f"<script>FrontBoil.init({opts_json});</script>",
    ]
    return mark_safe("\n".join(lines))


@register.simple_tag()
def moduloreactor_ui():
    """
    Inject container elements for toast, alert, and modal.
    Place this inside <body> — typically right before {% frontboil %}.

    Usage:
        {% load moduloreactor %}
        {% moduloreactor_ui %}
        {% frontboil %}

    Optional — containers are auto-created by JS if missing.
    This tag gives you explicit control over placement.
    """
    return mark_safe(
        '<div id="mr-toasts"></div>\n'
        '<div id="mr-alerts"></div>\n'
        '<div id="mr-modal-overlay"></div>'
    )
