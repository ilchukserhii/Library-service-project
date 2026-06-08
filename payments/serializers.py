from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import serializers

from payments.models import Payment


class PaymentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowings",
            "money_to_pay"
        )


class PaymentDetailSerializer(serializers.ModelSerializer):
    borrowings = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowings",
            "money_to_pay"
        )

    def get_borrowings(self, obj) -> dict:
        borrowing = obj.borrowings

        return {
            "borrow_date": borrowing.borrow_date,
            "expected_return_date": borrowing.expected_return_date,
            "actual_return_date": borrowing.actual_return_date,
            "book": borrowing.book.title,
        }
