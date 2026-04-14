# ModuloReactor — Usage Guide

## 1. Installation

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    "moduloreactor",
    # ...
]
```

## 2. Settings

```python
MODULOREACTOR = {
    # Optional: path to your Orchestrator class (for component rendering)
    "ORCHESTRATOR": "myapp.orchestrator.Orchestrator",

    # Toggle debug logging (server + client)
    "DEBUG": False,

    # Optional: override toast / alert / modal HTML (<template> fragments)
    # "UI_TEMPLATES": {
    #     "toast": "myapp/moduloreactor/ui/toast.html",
    #     "alert": "myapp/moduloreactor/ui/alert.html",
    #     "modal": "myapp/moduloreactor/ui/modal.html",
    # },
}
```

See **[messages-ui.md](messages-ui.md)** for toast, alert, `confirm`, `choice`, and template override contracts (`data-mr-*` hooks, required `<template id>` values).

## 3. URL Setup

```python
# project urls.py
from django.urls import include, path

urlpatterns = [
    path("fe-boiler/", include("moduloreactor.urls")),  # test page
    # ...
]
```

Visit `/fe-boiler/` to see the test playground.

## 4. Template Tag

```html
{% load moduloreactor %}
<!DOCTYPE html>
<html>
<body>
    <!-- your content -->
    {% frontboil %}
</body>
</html>
```

`{% frontboil %}` injects:
- **frontboil.css** (default toast / alert / modal styles)
- **HTML `<template>` fragments** for toast, alert, and modal (overridable via `UI_TEMPLATES`; see [messages-ui.md](messages-ui.md))
- **htmx.min.js** (local, no CDN)
- **frontboil.js** (event runtime)
- Init script

Options:
- `{% frontboil debug=True %}` — force debug mode on

## 5. Writing Actions

```python
from moduloreactor.handler import htmx_action

@htmx_action()
def my_action(h):
    # Read / write session
    count = h.get_session("counter", 0)
    h.set_session("counter", count + 1)

    # Emit events
    h.toast(f"Count: {count + 1}", "success")
    h.dom_update("#counter", f'<span id="counter">{count + 1}</span>')
```

Wire in urls.py:

```python
path("action/my-action/", views.my_action, name="my_action"),
```

Template form:

```html
<form hx-post="{% url 'my_action' %}" hx-swap="none">
    {% csrf_token %}
    <button type="submit">Do it</button>
</form>
```

**Important:** Always use `hx-swap="none"`. The event system handles all DOM updates.

## 6. Event System

### How it works

1. Form sends `hx-post` with `hx-swap="none"`
2. Server runs action, collects events
3. Response is JSON: `{"events": [...]}`
4. `frontboil.js` intercepts the JSON response
5. Each event is dispatched to its registered handler

### Built-in events

| Event | Fields | Behaviour |
|-------|--------|-----------|
| `dom.update` | `target`, `html`, `swap?`, `many?` | Replace element content. swap: `outerHTML` (default), `innerHTML`, `beforeend`, `afterbegin`. If `many` is true, every element matching `target` is updated; otherwise only the first match (default). |
| `dom.remove` | `target`, `many?` | Remove from DOM. If `many` is true, every match is removed; otherwise only the first match (default). |
| `toast` | `message`, `level?`, `duration?` | Show floating toast. level: `info`, `success`, `warning`, `error`. Default duration: 3000ms |
| `alert` | `message`, `level?`, `dismissible?` | Show persistent alert banner. Click to dismiss (default) |
| `confirm` | `message`, `title?`, `on_confirm`, `on_cancel?`, `payload?`, `confirm_label?`, `cancel_label?`, `style?` | Modal: cancel + confirm; confirm POSTs to `on_confirm` with `payload`. |
| `choice` | `message`, `title?`, `options` | Modal: cancel + one button per option; each POSTs to `url` with optional `payload`. |
| `redirect` | `url` | Navigate to URL |
| `console` | `message` | `console.log` from server |

### Emitting events

```python
# Generic
h.emit("toast", {"message": "Hello", "level": "info"})

# Shortcuts
h.toast("Hello", "info")
h.alert("Warning!", "warning")
h.dom_update("#el", "<div id='el'>new</div>")
h.dom_append("#stream", "<div class='row'>appended</div>")  # same as dom_update(..., swap="beforeend")
h.dom_remove("#old")
h.redirect("/somewhere")
```

### Multi-target updates (`many=True`)

By default, `dom.update` / `dom.remove` affect only the **first** element that matches the CSS selector (same as `querySelector`). Pass `many=True` to update or remove **all** matches (`querySelectorAll`).

```python
# Two (or more) elements share a class or data attribute — update every match
h.dom_update(
    "[data-slot='status']",
    "<span>All slots refreshed</span>",
    swap="innerHTML",
    many=True,
)

h.dom_remove(".temporary-banner", many=True)
```

**HTML note:** duplicate `id` values are invalid HTML and unpredictable in the browser. Prefer classes or `data-*` attributes when you intentionally target multiple nodes.

### Custom events

Server:
```python
h.emit("my.custom.event", {"foo": "bar"})
```

Client:
```javascript
FrontBoil.on("my.custom.event", function(data) {
    console.log(data.foo);  // "bar"
});
```

### Processing events outside HTMX

For non-HTMX transports (e.g. `fetch`, websocket message handlers), use:

```javascript
window.ModuloReactor.processEvents([
  { type: "toast", message: "Hello", level: "success" }
]);
```

`window.FrontBoil` is still available for backward compatibility, but `window.ModuloReactor.processEvents(...)` is the stable public API for integrations.

## 7. Orchestrator Bridge (Optional)

If your project has a component orchestrator, you can render components from actions:

```python
@htmx_action()
def my_action(h):
    h.set_session("key", "value")
    h.render_components(["myapp.my-component", "core.toast-container"])
```

This requires `MODULOREACTOR["ORCHESTRATOR"]` in settings. The bridge calls the orchestrator, gets rendered HTML, and emits `dom.update` events automatically.

## 8. Handler API Reference

| Method | Description |
|--------|-------------|
| `h.get_session(key, default)` | Read from session |
| `h.set_session(key, value)` | Write to session |
| `h.del_session(key)` | Delete from session |
| `h.emit(type, data)` | Emit any event |
| `h.toast(message, level, duration, next)` | Emit toast |
| `h.alert(message, level, dismissible, next)` | Emit alert |
| `h.confirm(...)` | Emit confirm modal (see [messages-ui.md](messages-ui.md)) |
| `h.choice(message, options, title)` | Emit choice modal |
| `h.dom_update(target, html, swap, many)` | Emit DOM update (`many=False`: first match only) |
| `h.dom_append(target, html, many)` | Append HTML inside `target` (`beforeend` swap) |
| `h.dom_remove(target, many)` | Emit DOM removal (`many=False`: first match only) |
| `h.redirect(url)` | Emit redirect |
| `h.render_components(ids)` | Render via orchestrator |
| `h.POST` | Access `request.POST` |
| `h.GET` | Access `request.GET` |
| `h.request` | Raw Django request |

## 9. Debug Mode

### Enable

```python
MODULOREACTOR = {"DEBUG": True}
```

Or per-template:

```html
{% frontboil debug=True %}
```

### Server output

Uses Python's `logging` module, logger name: `moduloreactor`.

```python
LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "moduloreactor": {"handlers": ["console"], "level": "DEBUG"},
    },
}
```

Logs per action:
- Action name
- Events emitted
- Session mutations

### Client output

Open browser console. With debug enabled:
- `[FrontBoil:init]` — initialization
- `[FrontBoil:dispatch]` — each event dispatched
- `[FrontBoil:response]` — raw JSON payload

## 10. File Structure

```
moduloreactor/
├── __init__.py
├── apps.py
├── handler.py              # @htmx_action + HtmxHandler
├── ui_defaults.py          # Default UI template paths
├── events.py               # EventCollector
├── orchestrator_bridge.py  # Dynamic orchestrator loader
├── debug.py                # Debug logging
├── urls.py                 # Test page routes
├── views.py                # Test page actions
├── templatetags/
│   └── moduloreactor.py    # {% load moduloreactor %} → {% frontboil %}
├── static/moduloreactor/
│   ├── htmx.min.js         # Local HTMX 2.0.8 (no CDN)
│   └── frontboil.js        # Event-driven frontend runtime
├── templates/moduloreactor/
│   ├── test_page.html      # /fe-boiler test page
│   └── ui/                 # Default <template> overrides (toast / alert / modal)
├── docs/
│   ├── usage.md            # This file
│   └── messages-ui.md      # Toast, alert, confirm, choice + UI overrides
└── README.md
```
