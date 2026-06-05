from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingReadSerializer, BorrowingWriteSerializer, BorrowingAdminSerializer


class BorrowingsView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.all()
    authentication_classes = (JWTAuthentication,)

    def get_queryset(self):
        is_active = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")
        queryset = (
            Borrowing.objects
            .select_related("book", "user")
            .filter(user=self.request.user)
        )

        if self.request.user.is_staff:
            queryset = Borrowing.objects.select_related("book", "user")

        if is_active == "true":
            queryset = queryset.filter(actual_return_date__isnull=False)

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset


    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingWriteSerializer

        if self.request.user.is_staff :
            return BorrowingAdminSerializer

        return BorrowingReadSerializer

    def perform_create(self, serializer):
        book = serializer.validated_data["book"]

        book.inventory -= 1
        book.save()
        book.refresh_from_db()

        serializer.save(
            user=self.request.user,
            borrow_date=timezone.localdate(),
        )
