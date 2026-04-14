# Toast, alert, and dialogs (confirm / choice)

Server emits JSON events; `frontboil.js` mounts UI. Three paths:

| Event type | Python API | User-facing role |
|------------|------------|------------------|
| `toast` | `h.toast(message, level=..., duration=..., next=...)` | Short auto-dismiss notice (default 3000 ms). |
| `alert` | `h.alert(message, level=..., dismissible=..., next=...)` | Persistent banner (click to dismiss if `dismissible=True`). |
| `confirm` | `h.confirm(message, on_confirm, payload=..., ...)` | Two actions: cancel + confirm; confirm POSTs to `on_confirm`. |
| `choice` | `h.choice(message, options, title=...)` | Modal with cancel + one button per `options[]`; each POSTs to its `url`. |

**Levels** (toast + alert): `info`, `success`, `warning`, `error` — map to CSS classes `mr-toast--{level}` / `mr-alert--{level}`.

**Confirm payload fields** (JSON under `confirm`):

- `message`, `title`, `on_confirm`, `on_cancel`, `payload`, `confirm_label`, `cancel_label`, `style` (`default` | `danger` on confirm button).

**Choice payload fields** (JSON under `choice`):

- `message`, `title`, `options`: list of `{ label, url, payload?, style? }`.

---

## How markup gets on the page

1. `{% frontboil %}` renders three hidden `<template>` blocks (toast, alert, modal shell) **before** `frontboil.js` loads.
2. On each event, JS **clones** the matching template, fills `data-mr-*` slots, appends to `#mr-toasts`, `#mr-alerts`, or `#mr-modal-overlay`.
3. If a `<template id="mr-ui-tpl-*">` is missing, JS falls back to the built-in `document.createElement` layout (same look as before overrides).

Containers `#mr-toasts`, `#mr-alerts`, `#mr-modal-overlay` come from `{% moduloreactor_ui %}` or are auto-created by JS.

---

## Override with Django templates

In `settings.py`:

```python
MODULOREACTOR = {
    "DEBUG": False,
    "UI_TEMPLATES": {
        "toast": "myapp/moduloreactor/ui/toast.html",
        "alert": "myapp/moduloreactor/ui/alert.html",
        "modal": "myapp/moduloreactor/ui/modal.html",
    },
}
```

Keys omitted keep package defaults (`moduloreactor/ui/toast.html`, etc.). Put your files under `myapp/templates/...` (or any app on `DIRS` / app loaders).

**Rules:**

1. Each file must output **exactly one** root `<template id="...">` … `</template>` with the ids below (FrontBoil looks them up by id).
2. Keep the **documented `data-mr-*` attributes** so JS can bind text and (for modal) inject buttons into the actions row.
3. You may add extra markup/classes inside the clone root; default CSS targets `.mr-toast`, `.mr-alert`, `.mr-modal`, `.mr-btn`.

---

### Toast override — required structure

- **Outer:** `<template id="mr-ui-tpl-toast">`
- **Inner root:** any element with `data-mr-toast-root` (gets `mr-toast--{level}` added at runtime).
- **Message node:** element with `data-mr-toast-message` (text filled from event `message`).

Example (minimal):

```html
<template id="mr-ui-tpl-toast">
  <div class="mr-toast" data-mr-toast-root role="status" aria-live="polite">
    <span data-mr-toast-message></span>
  </div>
</template>
```

---

### Alert override — required structure

- **Outer:** `<template id="mr-ui-tpl-alert">`
- **Inner root:** `data-mr-alert-root` (gets `mr-alert--{level}`; may get `mr-alert--dismissible` when dismissible).
- **Message:** `data-mr-alert-message`

Example:

```html
<template id="mr-ui-tpl-alert">
  <div class="mr-alert" data-mr-alert-root role="alert">
    <span data-mr-alert-message></span>
  </div>
</template>
```

---

### Modal override (confirm + choice) — required structure

Same shell for both. JS fills title/message and **appends** `<button type="button" class="mr-btn mr-btn--...">` into the actions container.

- **Outer:** `<template id="mr-ui-tpl-modal">`
- **Card root:** `data-mr-modal-root` (usually `.mr-modal`)
- **Title:** `data-mr-modal-title` — `hidden` when no title
- **Body:** `data-mr-modal-message`
- **Buttons row:** `data-mr-modal-actions` — emptied then buttons appended in order

Example:

```html
<template id="mr-ui-tpl-modal">
  <div class="mr-modal" data-mr-modal-root>
    <div class="mr-modal__title" data-mr-modal-title hidden></div>
    <div class="mr-modal__message" data-mr-modal-message></div>
    <div class="mr-modal__actions" data-mr-modal-actions></div>
  </div>
</template>
```

Button labels/styles still come from server (`confirm_label`, `style` on options, etc.); only layout/wrappers are template-driven.

---

## Styling without replacing templates

Override or extend **[`frontboil.css`](../static/moduloreactor/frontboil.css)** by loading your CSS **after** `{% frontboil %}` (same class names), or replace the link via forking static files / collectstatic overrides.

---

## `next=True` (queue for next full page load)

`h.toast(..., next=True)` and `h.alert(..., next=True)` store events in session; `{% frontboil %}` drains them into `FrontBoil.init({ nextMessages: [...] })` so they run once on load. Same event shapes; same template clone path applies.
