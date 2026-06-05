from django.utils import timezone
from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
        )


class BorrowingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "expected_return_date",
            "book"
        )

    def validate(self, attrs):
        borrow_date = timezone.localdate()
        expected_return_date = attrs["expected_return_date"]
        book = attrs["book"]

        if book.inventory < 1:
            raise serializers.ValidationError(
                "Book inventory can't be less than 1"
            )

        if expected_return_date < borrow_date:
            raise serializers.ValidationError(
                "Expected return date must be after borrow date"
            )

        return attrs
