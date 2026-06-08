from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import PaymentListSerializer, PaymentDetailSerializer

PAYMENTS_URL = reverse("payments:payments-list")


def get_detail_url(payment):
    return reverse("payments:payments-detail", args=[payment.id])


def sample_book(**params):
    defaults = {
        "title": "Sample Book",
        "author": "Test Author",
        "cover": "SOFT",
        "inventory": 10,
        "daily_fee": 2.50
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def sample_borrowing(**params):
    book = sample_book()
    tomorrow = timezone.localdate() + timedelta(days=1)
    defaults = {
        "borrow_date": timezone.localdate(),
        "expected_return_date": tomorrow,
        "book": book,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


def sample_user(**params):
    defaults = {
        "email": "user@email.com",
        "password": "password",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


class PaymentUserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@user.com",
            password="testpass"
        )
        self.client.force_authenticate(self.user)

    def test_list_view(self):
        borrowing = sample_borrowing(
            user=self.user,
        )
        payment = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowings=borrowing,
            money_to_pay=2.50
        )

        response = self.client.get(PAYMENTS_URL)

        serializer = PaymentListSerializer(payment)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0], serializer.data)

    def test_detail_view(self):
        borrowing = sample_borrowing(
            user=self.user,
        )
        payment = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowings=borrowing,
            money_to_pay=2.50
        )

        response = self.client.get(get_detail_url(payment))

        serializer = PaymentDetailSerializer(payment)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_user_can_see_only_own_payments(self):
        borrowing_1 = sample_borrowing(
            user=self.user,
        )
        some_user = sample_user()
        borrowing_2 = sample_borrowing(
            user=some_user,
        )
        payment_1 = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowings=borrowing_1,
            money_to_pay=2.50
        )
        payment_2 = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowings=borrowing_2,
            money_to_pay=2.50
        )
        response = self.client.get(PAYMENTS_URL)
        serializer_1 = PaymentListSerializer([payment_1], many=True)
        serializer_2 = PaymentListSerializer([payment_2], many=True)
        self.assertEqual(response.data["results"], serializer_1.data)
        self.assertNotEqual(response.data["results"], serializer_2.data)

    def test_action_cancel_payment(self):
        response = self.client.get(PAYMENTS_URL + "cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            response.data["detail"],
            "Payment can be made later. Session is available for 24 hours."
        )

    @patch("payments.views.client.v1.checkout.sessions.retrieve")
    def test_success_payment_sets_status_paid(self, mock_retrieve):
        borrowing = sample_borrowing(user=self.user)

        payment = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowings=borrowing,
            session_id="cs_test_123",
            session_url="https://checkout.stripe.com/test",
            money_to_pay=2.50,
        )

        mock_session = MagicMock()
        mock_session.payment_status = "paid"
        mock_retrieve.return_value = mock_session

        response = self.client.get(
            PAYMENTS_URL + "success/",
            {"session_id": "cs_test_123"},
        )

        payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment.status, "PAID")
        self.assertEqual(response.data["status"], "PAID")
