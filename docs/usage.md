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
}
```

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
| `dom.update` | `target`, `html`, `swap?` | Replace element content. swap: `outerHTML` (default), `innerHTML`, `beforeend`, `afterbegin` |
| `dom.remove` | `target` | Remove element from DOM |
| `toast` | `message`, `level?`, `duration?` | Show floating toast. level: `info`, `success`, `warning`, `error`. Default duration: 3000ms |
| `alert` | `message`, `level?`, `dismissible?` | Show persistent alert banner. Click to dismiss (default) |
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
h.dom_remove("#old")
h.redirect("/somewhere")
```

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
| `h.toast(message, level)` | Emit toast |
| `h.alert(message, level, dismissible)` | Emit alert |
| `h.dom_update(target, html, swap)` | Emit DOM update |
| `h.dom_remove(target)` | Emit DOM removal |
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
│   └── test_page.html      # /fe-boiler test page
├── docs/
│   └── usage.md            # This file
└── README.md
```
