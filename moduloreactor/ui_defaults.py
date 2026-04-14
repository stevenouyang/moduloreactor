"""Default Django template paths for FrontBoil UI (<template> fragments)."""

DEFAULT_TOAST_TEMPLATE = "moduloreactor/ui/toast.html"
DEFAULT_ALERT_TEMPLATE = "moduloreactor/ui/alert.html"
DEFAULT_MODAL_TEMPLATE = "moduloreactor/ui/modal.html"


def resolve_ui_template_paths(config):
    """
    Return dict toast, alert, modal -> template path string.
    config is MODULOREACTOR settings dict.
    """
    ui = config.get("UI_TEMPLATES") or {}
    return {
        "toast": ui.get("toast", DEFAULT_TOAST_TEMPLATE),
        "alert": ui.get("alert", DEFAULT_ALERT_TEMPLATE),
        "modal": ui.get("modal", DEFAULT_MODAL_TEMPLATE),
    }
