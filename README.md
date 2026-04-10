# Modulo Reactor

Event-driven HTMX integration for Django. Drop-in package.
Server renders, events drive UI. No SPA, no build step.

## Quick Start

```python
# settings.py
INSTALLED_APPS = ["moduloreactor", ...]

MODULOREACTOR = {
    "ORCHESTRATOR": "myapp.orchestrator.Orchestrator",  # optional
    "DEBUG": True,
}
```

```python
# urls.py
path("fe-boiler/", include("moduloreactor.urls")),  # test page
```

```html
{% load moduloreactor %}
{% frontboil %}
```

```python
from moduloreactor.handler import htmx_action

@htmx_action()
def my_action(h):
    h.set_session("key", "value")
    h.toast("Saved!", "success")
    h.dom_update("#target", "<div id='target'>Done</div>")
```

## Hosting / Deployment

ModuloReactor is a standard Django app — it deploys wherever Django runs.

### Strategy 1: Monorepo (recommended for teams)

Keep `moduloreactor/` inside your Django project. Copy it across projects.

```
myproject/
    moduloreactor/   ← just copy this folder
    myapp/
    manage.py
```

### Strategy 2: Private Git Subtree / Submodule

```bash
# subtree (recommended)
git subtree add --prefix=moduloreactor git@github.com:you/moduloreactor.git main

# or submodule
git submodule add git@github.com:you/moduloreactor.git moduloreactor
```

### Strategy 3: Private PyPI Package

```bash
pip install moduloreactor --index-url https://your-private-pypi/simple/
```

Create `pyproject.toml` at package root:

```toml
[project]
name = "moduloreactor"
version = "0.1.0"
dependencies = ["django>=4.2"]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends._legacy:_Backend"
```

### Strategy 4: Direct pip from Git

```bash
pip install git+ssh://git@github.com/you/moduloreactor.git
```

### Production Checklist

- Set `MODULOREACTOR["DEBUG"] = False` in production
- Run `python manage.py collectstatic` to collect htmx.min.js + frontboil.js
- Serve static files via nginx / whitenoise / CDN
- The `/fe-boiler/` test page is optional — remove from `urls.py` in production if desired

See [docs/usage.md](docs/usage.md) for full documentation.
