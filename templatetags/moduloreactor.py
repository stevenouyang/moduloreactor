import json

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()


def _get_config():
    return getattr(settings, "MODULOREACTOR", {})


@register.simple_tag(takes_context=True)
def frontboil(context, debug=None):
    """
    Auto-inject HTMX + FrontBoil JS + CSS + next-message queue.

    Usage:
        {% load moduloreactor %}
        {% frontboil %}
        {% frontboil debug=True %}
    """
    config = _get_config()
    if debug is None:
        debug = config.get("DEBUG", False)

    htmx_url = static("moduloreactor/htmx.min.js")
    fb_js = static("moduloreactor/frontboil.js")
    fb_css = static("moduloreactor/frontboil.css")

    hashes_json = context.get("component_hashes", "{}")

    # Build init options
    opts = {}
    if debug:
        opts["debug"] = True

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

    lines = [
        f'<link rel="stylesheet" href="{fb_css}">',
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
