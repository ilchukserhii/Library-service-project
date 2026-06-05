from django.urls import path, include
from rest_framework import routers

from borrowings.views import BorrowingsView

app_name = "borrowings"

router = routers.DefaultRouter()
router.register("borrowings", BorrowingsView, basename="borrowings")

urlpatterns = [
    path("", include(router.urls)),
]
