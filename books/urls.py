from django.urls import path, include
from rest_framework import routers

from books.views import BookView

app_name = "books"

router = routers.DefaultRouter()
router.register("books", BookView, basename="book")

urlpatterns = [
    path("", include(router.urls)),
]
