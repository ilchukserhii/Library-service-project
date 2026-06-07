from django.urls import path, include
from rest_framework import routers

from payments.views import PaymentsView


app_name = "payments"

router = routers.DefaultRouter()
router.register("payments", PaymentsView, basename="payments")

urlpatterns = [
    path("", include(router.urls)),
]
