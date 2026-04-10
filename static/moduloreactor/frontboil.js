/**
 * FrontBoil — Event-driven HTMX frontend runtime
 *
 * Responsibilities:
 *  1. Intercept HTMX JSON responses and dispatch events
 *  2. Provide built-in handlers: dom.update, toast, alert, redirect, dom.remove
 *  3. Allow custom event handlers via FrontBoil.on()
 *  4. Attach X-Component-Hashes header to requests (orchestrator compat)
 *  5. Debug logging (toggleable)
 */
(function () {
    "use strict";

    var FrontBoil = {
        debug: false,
        hashes: {},
        _handlers: {},

        // ── Init ──────────────────────────────────────────────

        init: function (options) {
            options = options || {};
            this.debug = !!options.debug;
            this.hashes = options.hashes || {};
            this._bindHtmx();
            this._registerDefaults();
            this._log("init", options);
        },

        // ── Public API ────────────────────────────────────────

        on: function (eventType, handler) {
            if (!this._handlers[eventType]) {
                this._handlers[eventType] = [];
            }
            this._handlers[eventType].push(handler);
        },

        dispatch: function (eventType, data) {
            var fns = this._handlers[eventType] || [];
            this._log("dispatch", { type: eventType, data: data, handlers: fns.length });
            for (var i = 0; i < fns.length; i++) {
                fns[i](data);
            }
        },

        // ── HTMX Binding ─────────────────────────────────────

        _bindHtmx: function () {
            var self = this;

            document.body.addEventListener("htmx:configRequest", function (evt) {
                if (Object.keys(self.hashes).length) {
                    evt.detail.headers["X-Component-Hashes"] = JSON.stringify(self.hashes);
                }
            });

            document.body.addEventListener("htmx:beforeSwap", function (evt) {
                var xhr = evt.detail.xhr;
                if (!xhr) return;
                var ct = xhr.getResponseHeader("Content-Type") || "";
                if (ct.indexOf("application/json") === -1) return;

                // JSON response — prevent htmx swap, we handle it
                evt.detail.shouldSwap = false;

                try {
                    var payload = JSON.parse(xhr.responseText);
                    self._log("response", payload);
                    if (payload.events && payload.events.length) {
                        self._processEvents(payload.events);
                    }
                    if (payload.hashes) {
                        Object.assign(self.hashes, payload.hashes);
                    }
                } catch (e) {
                    self._log("error", "Failed to parse response: " + e.message);
                }
            });
        },

        _processEvents: function (events) {
            for (var i = 0; i < events.length; i++) {
                this.dispatch(events[i].type, events[i]);
            }
        },

        // ── Built-in Event Handlers ──────────────────────────

        _registerDefaults: function () {

            // dom.update — swap HTML into a target
            this.on("dom.update", function (e) {
                var target = document.querySelector(e.target);
                if (!target) return;
                var swap = e.swap || "outerHTML";
                if (swap === "outerHTML") {
                    target.outerHTML = e.html;
                } else if (swap === "innerHTML") {
                    target.innerHTML = e.html;
                } else if (swap === "beforeend") {
                    target.insertAdjacentHTML("beforeend", e.html);
                } else if (swap === "afterbegin") {
                    target.insertAdjacentHTML("afterbegin", e.html);
                }
                if (typeof htmx !== "undefined") {
                    htmx.process(document.querySelector(e.target) || document.body);
                }
            });

            // dom.remove
            this.on("dom.remove", function (e) {
                var target = document.querySelector(e.target);
                if (target) target.remove();
            });

            // toast
            this.on("toast", function (e) {
                var container = document.getElementById("frontboil-toasts");
                if (!container) {
                    container = document.createElement("div");
                    container.id = "frontboil-toasts";
                    container.style.cssText =
                        "position:fixed;top:1rem;right:1rem;z-index:9999;" +
                        "display:flex;flex-direction:column;gap:0.5rem;pointer-events:none;";
                    document.body.appendChild(container);
                }
                var toast = document.createElement("div");
                var level = e.level || "info";
                var bg =
                    level === "success" ? "#16a34a" :
                    level === "error"   ? "#dc2626" :
                    level === "warning" ? "#d97706" : "#2563eb";
                toast.style.cssText =
                    "padding:0.75rem 1.25rem;border-radius:0.5rem;color:#fff;" +
                    "font-size:0.875rem;pointer-events:auto;cursor:pointer;" +
                    "box-shadow:0 4px 12px rgba(0,0,0,.15);background:" + bg + ";";
                toast.textContent = e.message;
                toast.onclick = function () { toast.remove(); };
                container.appendChild(toast);
                var dur = e.duration || 3000;
                setTimeout(function () { if (toast.parentNode) toast.remove(); }, dur);
            });

            // alert
            this.on("alert", function (e) {
                var container = document.getElementById("frontboil-alerts");
                if (!container) {
                    container = document.createElement("div");
                    container.id = "frontboil-alerts";
                    container.style.cssText =
                        "position:fixed;bottom:1rem;left:50%;transform:translateX(-50%);" +
                        "z-index:9998;display:flex;flex-direction:column;gap:0.5rem;" +
                        "max-width:600px;width:calc(100% - 2rem);";
                    document.body.appendChild(container);
                }
                var level = e.level || "info";
                var colors = {
                    success: { bg: "#f0fdf4", border: "#16a34a", text: "#166534" },
                    error:   { bg: "#fef2f2", border: "#dc2626", text: "#991b1b" },
                    warning: { bg: "#fffbeb", border: "#d97706", text: "#92400e" },
                    info:    { bg: "#eff6ff", border: "#2563eb", text: "#1e40af" },
                };
                var c = colors[level] || colors.info;
                var el = document.createElement("div");
                el.style.cssText =
                    "padding:0.75rem 1rem;border-radius:0.5rem;border:1px solid " + c.border +
                    ";background:" + c.bg + ";color:" + c.text + ";font-size:0.875rem;";
                el.textContent = e.message;
                if (e.dismissible !== false) {
                    el.style.cursor = "pointer";
                    el.onclick = function () { el.remove(); };
                }
                container.appendChild(el);
            });

            // redirect
            this.on("redirect", function (e) {
                if (e.url) window.location.href = e.url;
            });

            // console (debug helper)
            this.on("console", function (e) {
                console.log("[FrontBoil:server]", e.message || e);
            });
        },

        // ── Debug ─────────────────────────────────────────────

        _log: function (ctx, data) {
            if (this.debug) {
                console.log("[FrontBoil:" + ctx + "]", data);
            }
        }
    };

    window.FrontBoil = FrontBoil;
})();
