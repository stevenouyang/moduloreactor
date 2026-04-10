"""
Test page views for /fe-boiler.

These exist purely for development, debugging, and documentation.
They demonstrate all event types: dom.update, toast, alert, redirect, dom.remove.
"""
from django.shortcuts import render

from .handler import htmx_action


def test_page(request):
    """Render the FrontBoil test/playground page."""
    return render(request, "moduloreactor/test_page.html", {
        "counter": request.session.get("_fb_counter", 0),
        "items": request.session.get("_fb_items", ["Buy groceries", "Read a book", "Write code"]),
        "status": request.session.get("_fb_status", "online"),
    })


# ── Actions ─────────────────────────────────────────────────


@htmx_action()
def test_counter(h):
    action = h.POST.get("action", "increment")
    count = h.get_session("_fb_counter", 0)
    count = count + 1 if action == "increment" else count - 1
    h.set_session("_fb_counter", count)
    h.toast(f"Counter: {count}", "success")
    h.dom_update("#counter-value", f'<span id="counter-value">{count}</span>')


@htmx_action()
def test_add_item(h):
    name = h.POST.get("item_name", "").strip()
    if not name:
        h.toast("Item name is required", "warning")
        return
    items = h.get_session("_fb_items", ["Buy groceries", "Read a book", "Write code"])
    items.append(name)
    h.set_session("_fb_items", items)
    h.toast(f'Added "{name}"', "success")
    html = "".join(f"<li>{item}</li>" for item in items)
    h.dom_update("#item-list", f'<ul id="item-list">{html}</ul>')


@htmx_action()
def test_set_status(h):
    status = h.POST.get("status", "online")
    if status not in ("online", "away", "busy"):
        status = "online"
    h.set_session("_fb_status", status)
    colors = {"online": "#16a34a", "away": "#d97706", "busy": "#dc2626"}
    color = colors.get(status, "#6b7280")
    h.toast(f"Status → {status}", "info")
    h.dom_update(
        "#status-indicator",
        f'<span id="status-indicator" style="color:{color};font-weight:bold">'
        f"{status.upper()}</span>",
    )


@htmx_action()
def test_toast(h):
    message = h.POST.get("message", "Hello!")
    level = h.POST.get("level", "info")
    h.toast(message, level)


@htmx_action()
def test_alert(h):
    message = h.POST.get("message", "Watch out!")
    level = h.POST.get("level", "info")
    h.alert(message, level)
