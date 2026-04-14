from django.core.management.base import BaseCommand
from django.conf import settings


PENJELASAN = """
================================================================================
  MODULOREACTOR — Panduan Lengkap (Bahasa Indonesia)
================================================================================

  Apa sih ModuloReactor?
  ----------------------
  Package Django yang bikin kamu bisa bangun UI interaktif pake HTMX
  tanpa ribet. Gak pake SPA, gak pake build step, gak pake npm.
  Semua dihandle server-side, tapi UI-nya tetep responsif kayak SPA.

  Konsep utamanya: EVENT-DRIVEN.
  Server nge-emit event, frontend nge-dispatch, DOM ke-update.
  Sesimpel itu.

================================================================================
  CARA KERJA
================================================================================

  1. User klik tombol / submit form
     └─> HTMX kirim POST request ke server

  2. Server jalanin @htmx_action, kumpulin events
     └─> h.toast("Berhasil!", "success")
     └─> h.dom_update("#target", "<div>baru</div>")

  3. Server balikin JSON: {{"events": [...]}}
     └─> frontboil.js intercept response-nya

  4. frontboil.js dispatch setiap event
     └─> DOM ke-update, toast muncul, dst.

  PENTING: Semua form pake hx-swap="none"
  Karena yang handle DOM update itu event system, bukan HTMX swap.

================================================================================
  SETUP
================================================================================

  # settings.py
  INSTALLED_APPS = ["moduloreactor", ...]

  MODULOREACTOR = {{
      "ORCHESTRATOR": "myapp.orchestrator.Orchestrator",  # opsional
      "DEBUG": True,   # matiin di production
  }}

  # urls.py
  path("fe-boiler/", include("moduloreactor.urls")),  # test page

  # template
  {{% load moduloreactor %}}
  {{% frontboil %}}    <-- ini inject htmx.min.js + frontboil.js

================================================================================
  CARA PAKE DI VIEWS
================================================================================

  from moduloreactor.handler import htmx_action

  @htmx_action()
  def action_simpan(h):
      # Baca form data
      nama = h.POST.get("nama", "")

      # Session (baca / tulis / hapus)
      h.set_session("nama_user", nama)
      data = h.get_session("nama_user", "default")
      h.del_session("nama_user")

      # Update DOM — target pake CSS selector
      h.dom_update("#nama-display", '<span id="nama-display">Budi</span>')

      # Hapus element dari DOM
      h.dom_remove("#loading-spinner")

      # Toast notification (level: info, success, warning, error)
      h.toast("Data tersimpan!", "success")

      # Alert banner (persistent, klik untuk dismiss)
      h.alert("Perhatian: limit hampir habis", "warning")

      # Redirect
      h.redirect("/dashboard/")

      # Custom event (frontend bisa dengerin pake FrontBoil.on)
      h.emit("data.updated", {{"count": 42}})

================================================================================
  EVENT BAWAAN
================================================================================

  dom.update   — Update isi element di DOM
                 h.dom_update("#id", "<div id='id'>baru</div>")
                 swap: outerHTML (default), innerHTML, beforeend, afterbegin
                 many=True — update SEMUA element yang match selector (querySelectorAll)

  dom.remove   — Hapus element dari DOM
                 h.dom_remove("#element-id")
                 many=True — hapus SEMUA match selector

  toast        — Notifikasi floating (auto-hilang 3 detik)
                 h.toast("pesan", "success")

  alert        — Banner persistent (klik untuk dismiss)
                 h.alert("pesan", "error")

  redirect     — Pindah halaman
                 h.redirect("/halaman-lain/")

  console      — Log ke browser console (debugging)
                 h.emit("console", {{"message": "debug info"}})

================================================================================
  CUSTOM EVENT
================================================================================

  # Server (Python)
  h.emit("keranjang.update", {{"total": 5, "subtotal": 150000}})

  // Client (JavaScript)
  FrontBoil.on("keranjang.update", function(data) {{
      console.log("Total item:", data.total);
      // lakuin apa aja di sini
  }});

================================================================================
  TEMPLATE COMPONENTS (BEST PRACTICE)
================================================================================

  Pisahin HTML ke template kecil-kecil (atomic):

  templates/myapp/
  ├── index.html                    <-- halaman utama, pake {{% include %}}
  └── components/
      ├── product_card.html         <-- 1 card produk
      ├── cart_item.html            <-- 1 baris keranjang
      └── cart_total.html           <-- total harga

  Di views.py, JANGAN tulis HTML:

  from django.template.loader import render_to_string

  def _frag_card(product):
      return render_to_string("myapp/components/product_card.html", {{"p": product}})

  @htmx_action()
  def action_add_to_cart(h):
      # ... logic ...
      h.dom_update("#cart-items", _frag_cart_items(items))
      h.dom_update("#cart-total", _frag_cart_total(items))
      h.toast("Ditambahkan ke keranjang!", "success")

  Jadi HTML cuma di template, views cuma logic. Bersih.

================================================================================
  CSRF TOKEN
================================================================================

  frontboil.js OTOMATIS inject CSRF token ke semua HTMX request.
  Baca dari cookie "csrftoken", set ke header X-CSRFToken.

  Jadi kamu gak perlu {{% csrf_token %}} di setiap form HTMX.
  Cukup pastiin minimal 1x {{% csrf_token %}} ada di halaman
  (supaya Django set cookie-nya).

================================================================================
  STRUKTUR FILE PACKAGE
================================================================================

  moduloreactor/                         # distribution root (pyproject.toml)
  └── moduloreactor/                     # Django app — import moduloreactor
      ├── handler.py              <-- @htmx_action + HtmxHandler (API utama)
      ├── events.py               <-- EventCollector (kumpulin events)
      ├── orchestrator_bridge.py  <-- Load orchestrator dari settings
      ├── debug.py                <-- Debug logging
      ├── templatetags/
      │   └── moduloreactor.py    <-- {{% load moduloreactor %}} → {{% frontboil %}}
      ├── static/moduloreactor/
      │   ├── htmx.min.js         <-- HTMX local (no CDN)
      │   └── frontboil.js        <-- Event runtime frontend
      └── templates/moduloreactor/
          └── test_page.html      <-- /fe-boiler/ playground

================================================================================
  CONTOH REAL WORLD: testfront app
================================================================================

  Liat folder testfront/ sebagai contoh lengkap:

  testfront/
  ├── views.py                      <-- pure logic, gak ada HTML
  ├── urls.py                       <-- routing
  └── templates/testfront/
      ├── index.html                <-- layout, pake {{% include %}}
      └── components/
          ├── contact_row.html      <-- 1 baris tabel
          ├── contact_edit_row.html <-- inline edit form
          ├── contact_table_body.html <-- <tbody> wrapper
          └── contact_total.html    <-- counter badge

  Yang di-test:
  ✓ @htmx_action        ✓ h.toast          ✓ h.dom_update
  ✓ h.redirect          ✓ h.set_session    ✓ h.get_session
  ✓ h.del_session       ✓ h.emit           ✓ Multi dom.update
  ✓ Form validation     ✓ hx-confirm       ✓ Custom event
  ✓ render_to_string    ✓ Template components

================================================================================
  TIPS
================================================================================

  1. Semua form HTMX: hx-swap="none" (wajib!)
  2. HTML di template, logic di views — jangan campur
  3. Satu action bisa emit banyak event sekaligus
  4. Pake h.toast() buat feedback ke user
  5. Pake h.dom_update() buat update bagian halaman
  6. Debug mode: MODULOREACTOR["DEBUG"] = True
  7. Cek browser console buat liat event yang di-dispatch
  8. Production: matiin DEBUG, jalanin collectstatic
  9. Override markup toast/alert/modal: MODULOREACTOR["UI_TEMPLATES"] — docs/messages-ui.md

================================================================================
"""


class Command(BaseCommand):
    help = "Penjelasan lengkap package ModuloReactor dalam Bahasa Indonesia"

    def add_arguments(self, parser):
        parser.add_argument(
            "--singkat",
            action="store_true",
            help="Tampilkan versi singkat aja",
        )

    def handle(self, *args, **options):
        config = getattr(settings, "MODULOREACTOR", {})
        debug = config.get("DEBUG", False)
        orchestrator = config.get("ORCHESTRATOR", "tidak di-set")

        if options["singkat"]:
            self.stdout.write(self.style.SUCCESS("\n  ModuloReactor v0.2.0"))
            self.stdout.write(f"  Debug      : {'AKTIF' if debug else 'MATI'}")
            self.stdout.write(f"  Orchestrator: {orchestrator}")
            self.stdout.write("")
            self.stdout.write("  Cara pake:")
            self.stdout.write("    1. Tambahin 'moduloreactor' ke INSTALLED_APPS")
            self.stdout.write("    2. Set MODULOREACTOR di settings")
            self.stdout.write("    3. {% load moduloreactor %} + {% frontboil %} di template")
            self.stdout.write("    4. from moduloreactor.handler import htmx_action")
            self.stdout.write("    5. @htmx_action() di view, pake h.toast/h.dom_update/dll")
            self.stdout.write("")
            self.stdout.write("  Jalanin `python manage.py moduloreactor` tanpa --singkat")
            self.stdout.write("  buat penjelasan lengkap.\n")
            return

        self.stdout.write(PENJELASAN)

        self.stdout.write(self.style.SUCCESS("  STATUS SAAT INI:"))
        self.stdout.write(f"  Debug       : {'AKTIF ✓' if debug else 'MATI'}")
        self.stdout.write(f"  Orchestrator: {orchestrator}")
        self.stdout.write(f"  Test page   : /fe-boiler/")
        self.stdout.write(f"  Testfront   : /testfront/")
        self.stdout.write("")
