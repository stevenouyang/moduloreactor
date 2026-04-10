/**
 * FrontBoil — Event-driven HTMX frontend runtime
 *
 * Responsibilities:
 *  1. Intercept HTMX JSON responses and dispatch events
 *  2. Built-in handlers: dom.update, toast, alert, confirm, choice, redirect, dom.remove
 *  3. Custom event handlers via FrontBoil.on()
 *  4. Next-request message queue (rendered on page load)
 *  5. CSRF token auto-injection
 *  6. Debug logging (toggleable)
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
            this._processNextMessages(options.nextMessages || []);
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
                var csrfToken = self._getCookie("csrftoken");
                if (csrfToken) {
                    evt.detail.headers["X-CSRFToken"] = csrfToken;
                }
                if (Object.keys(self.hashes).length) {
                    evt.detail.headers["X-Component-Hashes"] = JSON.stringify(self.hashes);
                }
            });

            document.body.addEventListener("htmx:beforeSwap", function (evt) {
                var xhr = evt.detail.xhr;
                if (!xhr) return;
                var ct = xhr.getResponseHeader("Content-Type") || "";
                if (ct.indexOf("application/json") === -1) return;

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

        _processNextMessages: function (messages) {
            if (!messages || !messages.length) return;
            this._log("next-messages", messages);
            this._processEvents(messages);
        },

        // ── Built-in Event Handlers ──────────────────────────

        _registerDefaults: function () {
            var self = this;

            // ── dom.update ──
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

            // ── dom.remove ──
            this.on("dom.remove", function (e) {
                var target = document.querySelector(e.target);
                if (target) target.remove();
            });

            // ── toast ──
            this.on("toast", function (e) {
                var container = self._ensureEl("mr-toasts");
                var toast = document.createElement("div");
                var level = e.level || "info";
                toast.className = "mr-toast mr-toast--" + level;
                toast.textContent = e.message;
                toast.onclick = function () { toast.remove(); };
                container.appendChild(toast);
                var dur = e.duration || 3000;
                setTimeout(function () { if (toast.parentNode) toast.remove(); }, dur);
            });

            // ── alert ──
            this.on("alert", function (e) {
                var container = self._ensureEl("mr-alerts");
                var level = e.level || "info";
                var el = document.createElement("div");
                el.className = "mr-alert mr-alert--" + level;
                if (e.dismissible !== false) {
                    el.className += " mr-alert--dismissible";
                    el.onclick = function () { el.remove(); };
                }
                el.textContent = e.message;
                container.appendChild(el);
            });

            // ── confirm ──
            this.on("confirm", function (e) {
                self._showModal({
                    title: e.title,
                    message: e.message,
                    actions: [
                        {
                            label: e.cancel_label || "Cancel",
                            style: "secondary",
                            action: function () {
                                self._closeModal();
                                if (e.on_cancel) {
                                    self._postAction(e.on_cancel, e.payload || {});
                                }
                            }
                        },
                        {
                            label: e.confirm_label || "Confirm",
                            style: e.style || "default",
                            action: function () {
                                self._closeModal();
                                self._postAction(e.on_confirm, e.payload || {});
                            }
                        }
                    ]
                });
            });

            // ── choice ──
            this.on("choice", function (e) {
                var actions = [];
                actions.push({
                    label: "Cancel",
                    style: "secondary",
                    action: function () { self._closeModal(); }
                });
                var opts = e.options || [];
                for (var i = 0; i < opts.length; i++) {
                    (function (opt) {
                        actions.push({
                            label: opt.label,
                            style: opt.style || "default",
                            action: function () {
                                self._closeModal();
                                self._postAction(opt.url, opt.payload || {});
                            }
                        });
                    })(opts[i]);
                }
                self._showModal({
                    title: e.title,
                    message: e.message,
                    actions: actions
                });
            });

            // ── redirect ──
            this.on("redirect", function (e) {
                if (e.url) window.location.href = e.url;
            });

            // ── console ──
            this.on("console", function (e) {
                console.log("[FrontBoil:server]", e.message || e);
            });
        },

        // ── Modal ────────────────────────────────────────────

        _showModal: function (opts) {
            var self = this;
            var overlay = this._ensureEl("mr-modal-overlay");
            overlay.innerHTML = "";

            var modal = document.createElement("div");
            modal.className = "mr-modal";

            if (opts.title) {
                var title = document.createElement("div");
                title.className = "mr-modal__title";
                title.textContent = opts.title;
                modal.appendChild(title);
            }

            var msg = document.createElement("div");
            msg.className = "mr-modal__message";
            msg.textContent = opts.message;
            modal.appendChild(msg);

            var actions = document.createElement("div");
            actions.className = "mr-modal__actions";
            for (var i = 0; i < opts.actions.length; i++) {
                (function (a) {
                    var btn = document.createElement("button");
                    btn.className = "mr-btn mr-btn--" + (a.style || "default");
                    btn.textContent = a.label;
                    btn.onclick = a.action;
                    actions.appendChild(btn);
                })(opts.actions[i]);
            }
            modal.appendChild(actions);
            overlay.appendChild(modal);
            overlay.classList.add("mr-active");

            // Close on overlay click (outside modal)
            overlay.onclick = function (evt) {
                if (evt.target === overlay) self._closeModal();
            };
        },

        _closeModal: function () {
            var overlay = document.getElementById("mr-modal-overlay");
            if (overlay) overlay.classList.remove("mr-active");
        },

        // ── Utilities ────────────────────────────────────────

        _ensureEl: function (id) {
            var el = document.getElementById(id);
            if (!el) {
                el = document.createElement("div");
                el.id = id;
                document.body.appendChild(el);
            }
            return el;
        },

        _postAction: function (url, payload) {
            // Fire an HTMX-style POST via fetch, then process response events
            var self = this;
            var csrfToken = this._getCookie("csrftoken");
            var body = new FormData();
            if (payload) {
                for (var key in payload) {
                    if (payload.hasOwnProperty(key)) {
                        body.append(key, payload[key]);
                    }
                }
            }
            fetch(url, {
                method: "POST",
                headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
                body: body
            })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (data.events && data.events.length) {
                    self._processEvents(data.events);
                }
            })
            .catch(function (err) {
                self._log("error", "postAction failed: " + err.message);
            });
        },

        _getCookie: function (name) {
            var match = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
            return match ? decodeURIComponent(match[2]) : null;
        },

        _log: function (ctx, data) {
            if (this.debug) {
                console.log("[FrontBoil:" + ctx + "]", data);
            }
        }
    };

    window.FrontBoil = FrontBoil;
})();
