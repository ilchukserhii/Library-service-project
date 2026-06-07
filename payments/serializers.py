from rest_framework import serializers

from borrowings.serializers import BorrowingReadSerializer
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
    borrowings = BorrowingReadSerializer(many=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowings",
            "money_to_pay"
        )
