from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):
    class BookCover(models.TextChoices):
        HARD = "HARD", "Hard cover"
        SOFT = "SOFT", "Soft cover"
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    cover = models.CharField(
        max_length=10,
        choices=BookCover.choices
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return (
            f"{self.title}, author: {self.author} "
            f"(available: {self.inventory})"
        )
