import asyncio
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter, OpenApiResponse
)
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from borrowings.models import Borrowing
from borrowings.send_telegram_notification import send_telegram_notification
from borrowings.serializers import (
    BorrowingReadSerializer,
    BorrowingWriteSerializer,
    BorrowingAdminSerializer
)
from payments.stripe_payment import (
    create_payment_for_borrowing,
    create_fine_payment_for_borrowing
)


class BorrowingsView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Borrowing.objects.all()
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

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
            if user_id:
                queryset = queryset.filter(user_id=user_id)

        if is_active == "true":
            queryset = queryset.filter(actual_return_date__isnull=True)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                description=(
                    "Only for admin users: filter borrowings by user_id, "
                    "ex. ?user_id=1"
                ),
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                description="Filter borrowings by active, ex. ?is_active=true",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingWriteSerializer

        if self.request.user.is_staff:
            return BorrowingAdminSerializer

        return BorrowingReadSerializer

    def perform_create(self, serializer):
        book = serializer.validated_data["book"]

        book.inventory -= 1
        book.save()
        book.refresh_from_db()

        borrow = serializer.save(
            user=self.request.user,
            borrow_date=timezone.localdate(),
        )
        create_payment_for_borrowing(borrow, self.request)
        asyncio.run(send_telegram_notification(borrow))

    @extend_schema(
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Book returned successfully",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Borrowing already returned",
            )
        },
        description=(
            "Returns a borrowed book, sets actual_return_date, "
            "increases book inventory by 1, and creates a fine payment "
            "if the book is overdue."
        ),
    )
    @action(detail=True, methods=["post"], url_path="return")
    def return_book(self, request, pk=None):
        borrowing = self.get_object()
        if borrowing.actual_return_date is not None:
            return Response(
                "Borrowing already returned",
                status=status.HTTP_400_BAD_REQUEST,
            )
        borrowing.actual_return_date = timezone.localdate()
        if borrowing.actual_return_date > borrowing.expected_return_date:
            create_fine_payment_for_borrowing(borrowing, self.request)
        borrowing.book.inventory += 1
        borrowing.book.save()
        borrowing.save()
        return Response(
            "Book returned successfully",
            status=status.HTTP_200_OK
        )
