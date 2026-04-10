import json

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def frontboil(context, debug=None):
    """
    Auto-inject local HTMX + FrontBoil runtime.

    Usage:
        {% load moduloreactor %}
        {% frontboil %}
        {% frontboil debug=True %}
    """
    config = getattr(settings, "MODULOREACTOR", {})
    if debug is None:
        debug = config.get("DEBUG", False)

    htmx_url = static("moduloreactor/htmx.min.js")
    fb_url = static("moduloreactor/frontboil.js")

    hashes_json = context.get("component_hashes", "{}")

    opts = {}
    if debug:
        opts["debug"] = True

    # Merge hashes into options if present
    if hashes_json and hashes_json != "{}":
        opts_json = json.dumps(opts)
        # inject hashes as raw JS object (already JSON-serialised)
        opts_json = opts_json[:-1] + (', ' if opts else '') + '"hashes": ' + hashes_json + "}"
    else:
        opts_json = json.dumps(opts)

    lines = [
        f'<script src="{htmx_url}"></script>',
        f'<script src="{fb_url}"></script>',
        f"<script>FrontBoil.init({opts_json});</script>",
    ]
    return mark_safe("\n".join(lines))
