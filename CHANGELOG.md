# Changelog

## 0.3.1 - 2026-04-11

- Added optional `logUnhandled` runtime guardrail for custom events without handlers.
- Added template tag support for `log_unhandled` and settings key `MODULOREACTOR["LOG_UNHANDLED_EVENTS"]`.
- Kept default behavior unchanged (`logUnhandled` remains off unless enabled).

## 0.3.0 - 2026-04-11

- Added public frontend API `window.ModuloReactor.processEvents(events)` for non-HTMX transports.
- Kept `window.FrontBoil` compatibility while routing internal event callsites through the public processor.
- Added docs for "Using events outside HTMX" in package README and usage docs.
