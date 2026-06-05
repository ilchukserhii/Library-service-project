from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingReadSerializer, BorrowingWriteSerializer


class BorrowingsView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.all()
    authentication_classes = (JWTAuthentication,)

    def get_queryset(self):
        queryset = (
            Borrowing.objects
            .select_related("book", "user")
            .filter(user=self.request.user)
        )
        return queryset


    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return BorrowingReadSerializer
        return BorrowingWriteSerializer

    def perform_create(self, serializer):
        book = serializer.validated_data["book"]

        book.inventory -= 1
        book.save()
        book.refresh_from_db()

        serializer.save(
            user=self.request.user,
            borrow_date=timezone.localdate(),
        )
