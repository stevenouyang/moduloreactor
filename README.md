# Modulo Reactor

**Event-driven HTMX for Django** — server returns JSON events (or plain HTML partials); the browser updates the DOM. No SPA toolchain, no npm build.

**Author:** PT Claverio Data Pratama · **Current version:** `0.3.1`

---

## What it provides

| Piece | Role |
|--------|------|
| `@htmx_action` | Wraps a view: your function receives `h` and returns JSON `{"events":[...]}`. |
| `HtmxHandler` (`h`) | Emit toasts, alerts, modals, `dom.update` / `dom.remove` / `dom.append`, redirects, custom events. |
| `frontboil.js` | Hooks HTMX: JSON responses are **not** swapped by HTMX; events run through `FrontBoil` instead. |
| `{% frontboil %}` | Injects CSS, UI `<template>` fragments (toast / alert / modal), HTMX, `frontboil.js`, init (see [templatetags](moduloreactor/templatetags/moduloreactor.py)). |

---

## Requirements

- Python ≥ 3.10  
- Django ≥ 4.2  
- In templates that use ModuloReactor actions: load the tag library and include `{% frontboil %}` (typically end of `<body>`).

---

## Install

1. Add the app:

```python
# settings.py
INSTALLED_APPS = [
    "moduloreactor",
    # ...
]

MODULOREACTOR = {
    "ORCHESTRATOR": "myapp.orchestrator.Orchestrator",  # optional
    "DEBUG": False,
    "LOG_UNHANDLED_EVENTS": False,  # optional dev guardrail for custom events
}
```

2. Optional playground URL:

```python
# urls.py
path("fe-boiler/", include("moduloreactor.urls")),
```

3. In your base template:

```html
{% load moduloreactor %}
<body>
    {% moduloreactor_ui %}  {# optional: toast/alert/modal containers #}
    {# ... your content ... #}
    {% frontboil %}
</body>
```

Full reference: [docs/usage.md](moduloreactor/docs/usage.md).

**Toast / alert / confirm / choice** (payloads, `next=True`, overriding `<template>` markup): [docs/messages-ui.md](moduloreactor/docs/messages-ui.md).

---

## Two ways to use HTMX with ModuloReactor

Use **both** in the same project; they solve different problems.

### Pattern A — JSON actions (`@htmx_action`)

Use when the server should drive UI through **events** (toasts, several DOM patches, redirect, etc.).

1. Decorate the view with `@htmx_action()`.  
2. First argument is `h` (not `request`; use `h.request` if needed).  
3. Forms that POST to these URLs must use **`hx-swap="none"`** so HTMX does not try to swap HTML; FrontBoil reads the JSON body instead.

```python
from moduloreactor.handler import htmx_action

@htmx_action()
def save_widget(h):
    h.set_session("widget", h.POST.get("name", ""))
    h.toast("Saved", "success")
    h.dom_update("#widget-root", "<div id='widget-root'>…</div>")
    # Update every node matching a selector (prefer class or data-*; duplicate id is invalid HTML)
    h.dom_update("[data-status]", "<span data-status>ok</span>", swap="innerHTML", many=True)
```

```html
<form hx-post="{% url 'save_widget' %}" hx-swap="none">
    {% csrf_token %}
    <button type="submit">Save</button>
</form>
```

**DOM helpers (v0.2+):**

- `h.dom_update(selector, html, swap="outerHTML", many=False)` — `many=True` updates **all** matches.  
- `h.dom_remove(selector, many=False)` — `many=True` removes **all** matches.  
- `h.dom_append(selector, html, many=False)` — append inside each target when `many=True`.

Default `many=False` keeps the original behaviour (first match only).

### Pattern B — HTML partials (infinite scroll, “load more”, classic HTMX)

Use when the browser should **swap HTML** returned by the server (infinite scroll, pagination fragments, etc.).  
This is **normal Django**: a view returns `HttpResponse(html)` (or `render()` with a partial template). **Do not** use `@htmx_action` for that response — the client expects HTML, not `{"events":...}`.

**Infinite scroll (scroll sentinel)** is a common Pattern B setup:

1. First paint: a placeholder `div` with `hx-get="/your/feed/?page=1"`, `hx-trigger="revealed"`, `hx-swap="outerHTML"`.  
2. View for `/your/feed/` returns HTML that includes the next rows **and** a new bottom `div` with the same `hx-get` for `page=2`, etc., until you return an “end” snippet without a sentinel.  
3. HTMX performs the swap; FrontBoil **does not** treat the response as JSON (it only intercepts `Content-Type: application/json`).

Minimal example (Django view + attributes — align with `testfront` demo):

```python
# views.py — plain view, not @htmx_action
from django.http import HttpResponse
from django.template.loader import render_to_string

def feed_chunk(request):
    page = int(request.GET.get("page", 1))
    html = render_to_string("myapp/partials/feed_chunk.html", {"page": page, ...})
    return HttpResponse(html)
```

```html
<div
    hx-get="{% url 'feed_chunk' %}?page=1"
    hx-trigger="revealed"
    hx-swap="outerHTML"
    class="feed-sentinel"
>
    <p class="htmx-indicator">Scroll to load…</p>
</div>
```

**Why this coexists with ModuloReactor:** `frontboil.js` leaves non-JSON responses alone, so Pattern B keeps working on the same page as Pattern A forms.

---

## Using events outside HTMX

When your frontend transport is plain `fetch` (or anything non-HTMX), process server events with the public API:

```javascript
fetch("/chat/send/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "show toast" })
})
  .then(function (r) { return r.json(); })
  .then(function (data) {
    if (window.ModuloReactor && typeof window.ModuloReactor.processEvents === "function") {
      window.ModuloReactor.processEvents(data.events || []);
    }
  });
```

Compatibility notes:
- `window.FrontBoil` remains supported.
- `window.ModuloReactor.processEvents(events)` is the semver-stable surface for cross-package integrations.
- For custom events during development, enable `LOG_UNHANDLED_EVENTS` (or `{% frontboil log_unhandled=True %}`) to warn when an event has no registered `FrontBoil.on(...)` handler.

---

## Optional: orchestrator bridge

If `MODULOREACTOR["ORCHESTRATOR"]` is set, `h.render_components([...])` can render server components and emit `dom.update` for each id. See [usage.md §7](moduloreactor/docs/usage.md).

---

## Learn from the repo demos

| Demo | URL (typical) | What it shows |
|------|----------------|-----------------|
| ModuloReactor playground | `/fe-boiler/` | Counter, todos, tabs, toasts, `dom.update`, etc. |
| `testfront` app | `/testfront/` | Contacts CRUD, `many=True` mirror slots, **infinite scroll** (Pattern B), ModuloTalks sample |

---

## Hosting and distribution

ModuloReactor is a normal Django app: install it like any other local package or copy the `moduloreactor` package folder into your project.

```bash
python manage.py collectstatic   # ships htmx.min.js + frontboil.js
```

**Production:** set `MODULOREACTOR["DEBUG"] = False`; serve static files properly; remove `/fe-boiler/` from `urls.py` if you do not want the playground.

Example `pyproject.toml` for a vendored copy:

```toml
[project]
name = "moduloreactor"
version = "0.3.1"
dependencies = ["django>=4.2"]
authors = [{ name = "PT Claverio Data Pratama" }]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

Other install options (subtree, submodule, private PyPI, `pip install git+…`) are unchanged from typical Django packaging — see [docs/usage.md](moduloreactor/docs/usage.md) for file layout and logging.

---

## More documentation

- **[docs/usage.md](moduloreactor/docs/usage.md)** — event types, handler API, debug, `many=True`, forms.  
- **`python manage.py moduloreactor`** — long-form guide (Indonesian) in the management command.
