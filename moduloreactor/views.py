"""
ModuloReactor — Test / Demo views.

Comprehensive demo covering real-world patterns:
  - Counter (session state + DOM update)
  - Todo list (CRUD: add, toggle, delete, clear)
  - User profile card (multi-field form, multi-DOM update)
  - Notifications (toast & alert, all levels)
  - Tabs (swap inner content)
  - Inline edit (edit-in-place pattern)
  - Bulk actions (multi-event in one action)
  - Reset (clear all session state)
"""
import html as html_mod
from django.shortcuts import render

from .handler import htmx_action

# ── Defaults ────────────────────────────────────────────────

_DEFAULT_TODOS = [
    {"id": 1, "text": "Buy groceries", "done": False},
    {"id": 2, "text": "Read a book", "done": False},
    {"id": 3, "text": "Write code", "done": True},
]

_DEFAULT_PROFILE = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "role": "Developer",
    "bio": "Building things with Django + HTMX.",
}

_DEFAULT_TABS = {
    "overview": "This is the <strong>Overview</strong> tab. ModuloReactor uses an event-driven architecture — the server emits events, the client dispatches them.",
    "events": "The <strong>Events</strong> tab. Built-in types: <code>dom.update</code>, <code>toast</code>, <code>alert</code>, <code>redirect</code>, <code>dom.remove</code>. Register custom events with <code>FrontBoil.on()</code>.",
    "api": "The <strong>API</strong> tab. Use <code>@htmx_action()</code> to decorate views. The handler <code>h</code> gives you <code>h.emit()</code>, <code>h.toast()</code>, <code>h.dom_update()</code>, <code>h.set_session()</code>, and more.",
}


# ── Page ────────────────────────────────────────────────────


def test_page(request):
    todos = request.session.get("_mr_todos", _DEFAULT_TODOS)
    profile = request.session.get("_mr_profile", _DEFAULT_PROFILE)
    return render(request, "moduloreactor/test_page.html", {
        "counter": request.session.get("_mr_counter", 0),
        "todos": todos,
        "todo_count": len([t for t in todos if not t["done"]]),
        "profile": profile,
        "tab_content": _DEFAULT_TABS["overview"],
        "active_tab": "overview",
    })


# ── Counter ─────────────────────────────────────────────────


@htmx_action()
def action_counter(h):
    action = h.POST.get("action", "increment")
    count = h.get_session("_mr_counter", 0)
    if action == "increment":
        count += 1
    elif action == "decrement":
        count -= 1
    elif action == "reset":
        count = 0
    h.set_session("_mr_counter", count)
    h.dom_update(
        "#counter-value",
        f'<span id="counter-value" class="text-4xl font-bold tabular-nums'
        f' text-gray-900">{count}</span>',
    )


# ── Todo List ───────────────────────────────────────────────


def _render_todo_item(t):
    checked = "checked" if t["done"] else ""
    line_class = "line-through text-gray-400" if t["done"] else "text-gray-700"
    text = html_mod.escape(t["text"])
    return (
        f'<li id="todo-{t["id"]}" class="flex items-center gap-3 py-2 px-1'
        f' group border-b border-gray-100 last:border-0">'
        f'<form hx-post="/fe-boiler/action/todo-toggle/" hx-swap="none" class="contents">'
        f'<input type="hidden" name="todo_id" value="{t["id"]}">'
        f'<input type="checkbox" {checked} onchange="this.form.requestSubmit()"'
        f' class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer">'
        f'</form>'
        f'<span class="{line_class} flex-1 text-sm">{text}</span>'
        f'<form hx-post="/fe-boiler/action/todo-delete/" hx-swap="none" class="contents">'
        f'<input type="hidden" name="todo_id" value="{t["id"]}">'
        f'<button type="submit" class="opacity-0 group-hover:opacity-100 text-gray-400'
        f' hover:text-red-500 transition text-xs">✕</button>'
        f'</form>'
        f'</li>'
    )


def _render_todo_list(todos):
    if not todos:
        return ('<ul id="todo-list" class="divide-y divide-gray-100">'
                '<li class="py-4 text-center text-sm text-gray-400">No items yet</li></ul>')
    items = "".join(_render_todo_item(t) for t in todos)
    return f'<ul id="todo-list" class="divide-y divide-gray-100">{items}</ul>'


def _render_todo_count(todos):
    remaining = len([t for t in todos if not t["done"]])
    label = "item" if remaining == 1 else "items"
    return f'<span id="todo-count" class="text-xs text-gray-500">{remaining} {label} left</span>'


@htmx_action()
def action_todo_add(h):
    text = h.POST.get("text", "").strip()
    if not text:
        h.toast("Enter a task name", "warning")
        return
    todos = h.get_session("_mr_todos", _DEFAULT_TODOS)
    new_id = max((t["id"] for t in todos), default=0) + 1
    todos.append({"id": new_id, "text": text, "done": False})
    h.set_session("_mr_todos", todos)
    h.toast(f'Added "{text}"', "success")
    h.dom_update("#todo-list", _render_todo_list(todos))
    h.dom_update("#todo-count", _render_todo_count(todos))


@htmx_action()
def action_todo_toggle(h):
    todo_id = int(h.POST.get("todo_id", 0))
    todos = h.get_session("_mr_todos", _DEFAULT_TODOS)
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = not t["done"]
            break
    h.set_session("_mr_todos", todos)
    h.dom_update("#todo-list", _render_todo_list(todos))
    h.dom_update("#todo-count", _render_todo_count(todos))


@htmx_action()
def action_todo_delete(h):
    todo_id = int(h.POST.get("todo_id", 0))
    todos = h.get_session("_mr_todos", _DEFAULT_TODOS)
    todos = [t for t in todos if t["id"] != todo_id]
    h.set_session("_mr_todos", todos)
    h.toast("Removed", "info")
    h.dom_update("#todo-list", _render_todo_list(todos))
    h.dom_update("#todo-count", _render_todo_count(todos))


@htmx_action()
def action_todo_clear_done(h):
    todos = h.get_session("_mr_todos", _DEFAULT_TODOS)
    cleared = len([t for t in todos if t["done"]])
    todos = [t for t in todos if not t["done"]]
    h.set_session("_mr_todos", todos)
    if cleared:
        h.toast(f"Cleared {cleared} completed", "success")
    else:
        h.toast("Nothing to clear", "info")
    h.dom_update("#todo-list", _render_todo_list(todos))
    h.dom_update("#todo-count", _render_todo_count(todos))


# ── Profile Card ────────────────────────────────────────────


def _render_profile_display(profile):
    name = html_mod.escape(profile["name"])
    email = html_mod.escape(profile["email"])
    role = html_mod.escape(profile["role"])
    bio = html_mod.escape(profile["bio"])
    return (
        f'<div id="profile-card">'
        f'<div class="flex items-center gap-4 mb-4">'
        f'<div class="h-12 w-12 rounded-full bg-indigo-100 flex items-center justify-center'
        f' text-indigo-600 font-bold text-lg">{name[0]}</div>'
        f'<div>'
        f'<p class="font-semibold text-gray-900">{name}</p>'
        f'<p class="text-sm text-gray-500">{email}</p>'
        f'</div>'
        f'</div>'
        f'<div class="flex items-center gap-2 mb-2">'
        f'<span class="text-xs font-medium bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded">{role}</span>'
        f'</div>'
        f'<p class="text-sm text-gray-600 mb-4">{bio}</p>'
        f'<button hx-post="/fe-boiler/action/profile-edit-mode/" hx-swap="none"'
        f' class="text-sm text-indigo-600 hover:text-indigo-800 font-medium">Edit profile</button>'
        f'</div>'
    )


def _render_profile_form(profile):
    name = html_mod.escape(profile["name"])
    email = html_mod.escape(profile["email"])
    role = html_mod.escape(profile["role"])
    bio = html_mod.escape(profile["bio"])
    return (
        f'<form id="profile-card" hx-post="/fe-boiler/action/profile-save/" hx-swap="none" class="space-y-3">'
        f'<div><label class="block text-xs font-medium text-gray-500 mb-1">Name</label>'
        f'<input type="text" name="name" value="{name}"'
        f' class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"></div>'
        f'<div><label class="block text-xs font-medium text-gray-500 mb-1">Email</label>'
        f'<input type="email" name="email" value="{email}"'
        f' class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"></div>'
        f'<div><label class="block text-xs font-medium text-gray-500 mb-1">Role</label>'
        f'<input type="text" name="role" value="{role}"'
        f' class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"></div>'
        f'<div><label class="block text-xs font-medium text-gray-500 mb-1">Bio</label>'
        f'<textarea name="bio" rows="2"'
        f' class="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">{bio}</textarea></div>'
        f'<div class="flex gap-2">'
        f'<button type="submit" class="bg-indigo-600 text-white text-sm px-4 py-1.5 rounded-md hover:bg-indigo-700">Save</button>'
        f'<button type="button" hx-post="/fe-boiler/action/profile-cancel/" hx-swap="none"'
        f' class="text-sm text-gray-600 hover:text-gray-800 px-4 py-1.5 border border-gray-300 rounded-md">Cancel</button>'
        f'</div></form>'
    )


@htmx_action()
def action_profile_edit_mode(h):
    profile = h.get_session("_mr_profile", _DEFAULT_PROFILE)
    h.dom_update("#profile-card", _render_profile_form(profile))


@htmx_action()
def action_profile_save(h):
    profile = {
        "name": h.POST.get("name", "").strip() or "Anonymous",
        "email": h.POST.get("email", "").strip() or "n/a",
        "role": h.POST.get("role", "").strip() or "Member",
        "bio": h.POST.get("bio", "").strip() or "",
    }
    h.set_session("_mr_profile", profile)
    h.toast("Profile saved", "success")
    h.dom_update("#profile-card", _render_profile_display(profile))


@htmx_action()
def action_profile_cancel(h):
    profile = h.get_session("_mr_profile", _DEFAULT_PROFILE)
    h.dom_update("#profile-card", _render_profile_display(profile))


# ── Tabs ────────────────────────────────────────────────────


@htmx_action()
def action_tab(h):
    tab = h.POST.get("tab", "overview")
    content = _DEFAULT_TABS.get(tab, _DEFAULT_TABS["overview"])
    tabs = ["overview", "events", "api"]
    buttons = ""
    for t in tabs:
        active = "bg-indigo-600 text-white shadow-sm" if t == tab else "text-gray-600 hover:bg-gray-100"
        buttons += (
            f'<form hx-post="/fe-boiler/action/tab/" hx-swap="none" class="contents">'
            f'<input type="hidden" name="tab" value="{t}">'
            f'<button type="submit" class="px-4 py-1.5 text-sm font-medium rounded-md transition {active}">'
            f'{t.capitalize()}</button></form>'
        )
    h.dom_update(
        "#tab-buttons",
        f'<div id="tab-buttons" class="flex gap-1 bg-gray-50 p-1 rounded-lg">{buttons}</div>',
    )
    h.dom_update(
        "#tab-content",
        f'<div id="tab-content" class="text-sm text-gray-600 leading-relaxed p-4">{content}</div>',
    )


# ── Notifications ───────────────────────────────────────────


@htmx_action()
def action_toast(h):
    message = h.POST.get("message", "Hello!")
    level = h.POST.get("level", "info")
    h.toast(message, level)


@htmx_action()
def action_alert(h):
    message = h.POST.get("message", "Heads up!")
    level = h.POST.get("level", "info")
    h.alert(message, level)


# ── Bulk Demo (multi-event in one action) ───────────────────


@htmx_action()
def action_bulk_demo(h):
    h.toast("Step 1: Session updated", "info")
    h.toast("Step 2: Component refreshed", "success")
    h.alert("This is an alert from the same action", "info")
    h.dom_update(
        "#bulk-result",
        '<div id="bulk-result" class="text-sm text-green-700 bg-green-50'
        ' rounded-md p-3 border border-green-200">3 events fired from a single action.</div>',
    )


# ── Reset ───────────────────────────────────────────────────


@htmx_action()
def action_reset(h):
    for key in ["_mr_counter", "_mr_todos", "_mr_profile"]:
        h.del_session(key)
    h.toast("All state reset — reload to see defaults", "info")
    h.redirect("/fe-boiler/")
