from django.urls import path

from . import views

app_name = "moduloreactor"

urlpatterns = [
    path("", views.test_page, name="test_page"),
    # Counter
    path("action/counter/", views.action_counter, name="action_counter"),
    # Todo CRUD
    path("action/todo-add/", views.action_todo_add, name="action_todo_add"),
    path("action/todo-toggle/", views.action_todo_toggle, name="action_todo_toggle"),
    path("action/todo-delete/", views.action_todo_delete, name="action_todo_delete"),
    path("action/todo-clear/", views.action_todo_clear_done, name="action_todo_clear"),
    # Profile
    path("action/profile-edit-mode/", views.action_profile_edit_mode, name="action_profile_edit"),
    path("action/profile-save/", views.action_profile_save, name="action_profile_save"),
    path("action/profile-cancel/", views.action_profile_cancel, name="action_profile_cancel"),
    # Tabs
    path("action/tab/", views.action_tab, name="action_tab"),
    # Notifications
    path("action/toast/", views.action_toast, name="action_toast"),
    path("action/alert/", views.action_alert, name="action_alert"),
    # Bulk / Reset
    path("action/bulk/", views.action_bulk_demo, name="action_bulk"),
    path("action/reset/", views.action_reset, name="action_reset"),
]
