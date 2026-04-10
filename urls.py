from django.urls import path

from . import views

app_name = "moduloreactor"

urlpatterns = [
    path("", views.test_page, name="test_page"),
    path("action/counter/", views.test_counter, name="test_counter"),
    path("action/add-item/", views.test_add_item, name="test_add_item"),
    path("action/set-status/", views.test_set_status, name="test_set_status"),
    path("action/toast/", views.test_toast, name="test_toast"),
    path("action/alert/", views.test_alert, name="test_alert"),
]
