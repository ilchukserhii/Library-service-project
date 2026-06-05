from django.db import models
from django.db.models import F, Q

from library_service_api import settings


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(
        null=True,
        blank=True,
    )
    book = models.ForeignKey(
        "books.Book",
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(expected_return_date__gte=F("borrow_date")),
                name="expected_return_after_borrow"
            ),
            models.CheckConstraint(
                condition=(
                    Q(actual_return_date__isnull=True) |
                    Q(actual_return_date__gte=F("borrow_date"))
                ),
                name="actual_return_after_borrow"
            ),
        ]
        ordering = ["-borrow_date"]
