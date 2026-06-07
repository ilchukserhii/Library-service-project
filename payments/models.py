from django.db import models


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING"
        PAID = "PAID"

    class TypeChoices(models.TextChoices):
        PAYMENT = "PAYMENT"
        FINE = "FINE"
    status = models.CharField(
        choices=StatusChoices.choices,
        max_length=10
    )
    type = models.CharField(
        choices=TypeChoices.choices,
        max_length=10
    )
    borrowings = models.ForeignKey(
        "borrowings.Borrowing",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    session_url = models.URLField(max_length=500)
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    class Meta:
        ordering = ["-status"]
