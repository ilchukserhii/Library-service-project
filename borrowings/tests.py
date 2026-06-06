from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingWriteSerializer,
    BorrowingReadSerializer,
    BorrowingAdminSerializer
)

BORROWINGS_LIST_URL = reverse("borrowings:borrowings-list")


def detail_url(borrowing_id):
    return reverse("borrowings:borrowings-detail", args=[borrowing_id])


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


def sample_user(**params):
    defaults = {
        "email": "user@email.com",
        "password": "password",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


class BorrowingsModelTest(TestCase):
    def test_expected_return_date_cant_be_less_than_borrow_date(self):
        book = sample_book()
        user = sample_user()
        borrow_date = timezone.localdate()
        expected_return_date = borrow_date - timedelta(days=1)

        with self.assertRaises(IntegrityError):
            Borrowing.objects.create(
                borrow_date=borrow_date,
                expected_return_date=expected_return_date,
                actual_return_date=None,
                book=book,
                user=user
            )

    def test_actual_return_date_cant_be_less_than_borrow_date(self):
        book = sample_book()
        user = sample_user()
        borrow_date = timezone.localdate()
        actual_return_date = borrow_date - timedelta(days=1)

        with self.assertRaises(IntegrityError):
            Borrowing.objects.create(
                borrow_date=borrow_date,
                expected_return_date=borrow_date + timedelta(days=1),
                actual_return_date=actual_return_date,
                book=book,
                user=user,
            )


class BorrowingsSerializerTest(TestCase):
    def test_book_inventory_cant_be_less_than_1(self):
        book = sample_book(
            inventory=0,
        )
        tomorrow = timezone.localdate() + timedelta(days=1)
        serializer = BorrowingWriteSerializer(data={
            "expected_return_date": tomorrow,
            "book": book.id,
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Book inventory can't be less than 1",
            str(serializer.errors)
        )

    def test_expected_return_date_cant_be_less_than_borrow_date(self):
        book = sample_book()
        yesterday = timezone.localdate() - timedelta(days=1)
        serializer = BorrowingWriteSerializer(data={
            "expected_return_date": yesterday,
            "book": book.id,
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn(
            "Expected return date must be after borrow date",
            str(serializer.errors)
        )


class BorrowingAnautorizedViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_anautorized_view(self):
        response = self.client.get(BORROWINGS_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BorrowingAuthenticatedUserViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)

    def test_authenticated_user_list_view(self):
        book_1 = sample_book()
        book_2 = sample_book(
            title="title 2",
            author="Test Author 1",
        )
        tomorrow = timezone.localdate() + timedelta(days=1)
        Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=tomorrow,
            book=book_1,
            user=self.user,
        )
        Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=tomorrow,
            book=book_2,
            user=self.user,
        )

        response = self.client.get(BORROWINGS_LIST_URL)

        borrowings = Borrowing.objects.all()
        serializer = BorrowingReadSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_authenticated_user_detail_view(self):
        book = sample_book()
        tomorrow = timezone.localdate() + timedelta(days=1)
        borrow = Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=tomorrow,
            book=book,
            user=self.user,
        )

        response = self.client.get(detail_url(borrow.id))
        serializer = BorrowingReadSerializer(borrow)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_authenticated_user_create_borrow(self):
        book = sample_book()
        tomorrow = timezone.localdate() + timedelta(days=1)
        payload = {
            "expected_return_date": tomorrow,
            "book": book.id,
        }

        response = self.client.post(BORROWINGS_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)
        borrowing = Borrowing.objects.get()
        self.assertEqual(borrowing.user, self.user)
        self.assertEqual(borrowing.borrow_date, timezone.localdate())
        book.refresh_from_db()
        self.assertEqual(book.inventory, 9)

    def test_authenticated_user_filter_is_active(self):
        book = sample_book()
        tomorrow = timezone.localdate() + timedelta(days=1)
        borrow_1 = Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=tomorrow,
            book=book,
            user=self.user,
        )
        borrow_2 = Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=timezone.localdate(),
            actual_return_date=timezone.localdate(),
            book=book,
            user=self.user,
        )

        response = self.client.get(BORROWINGS_LIST_URL, {"is_active": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return_id = [item["id"] for item in response.data["results"]]
        self.assertIn(borrow_1.id, return_id)
        self.assertNotIn(borrow_2.id, return_id)

    def test_authenticated_user_return_book(self):
        book = sample_book()
        tomorrow = timezone.localdate() + timedelta(days=1)
        payload = {
            "expected_return_date": tomorrow,
            "book": book.id,
        }

        self.client.post(BORROWINGS_LIST_URL, payload)
        book.refresh_from_db()
        self.assertEqual(book.inventory, 9)
        borrow = Borrowing.objects.get()
        response = self.client.post(
            reverse(
                "borrowings:borrowings-return-book",
                args=[borrow.id]
            )
        )
        book.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(book.inventory, 10)

    def test_authenticated_user_cant_return_book_twice(self):
        book = sample_book()
        tomorrow = timezone.localdate() + timedelta(days=1)
        payload = {
            "expected_return_date": tomorrow,
            "book": book.id,
        }

        self.client.post(BORROWINGS_LIST_URL, payload)
        book.refresh_from_db()
        self.assertEqual(book.inventory, 9)
        borrow = Borrowing.objects.get()
        self.client.post(
            reverse(
                "borrowings:borrowings-return-book",
                args=[borrow.id]
            )
        )
        response = self.client.post(
            reverse(
                "borrowings:borrowings-return-book",
                args=[borrow.id]
            )
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BorrowingAdminViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@email.com",
            password="adminpass",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_admin_list_view(self):
        book_1 = sample_book()
        book_2 = sample_book(
            title="title 2",
            author="Test Author 1",
        )
        user1 = sample_user()
        user2 = sample_user(
            email="user2@email.com",
            password="pass2",
        )
        tomorrow = timezone.localdate() + timedelta(days=1)
        Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=tomorrow,
            book=book_1,
            user=user1,
        )
        Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=tomorrow,
            book=book_2,
            user=user2,
        )

        response = self.client.get(BORROWINGS_LIST_URL)
        borrowings = Borrowing.objects.all()
        serializer = BorrowingAdminSerializer(borrowings, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_admin_filter_iser_id(self):
        book_1 = sample_book()
        book_2 = sample_book(
            title="title 2",
            author="Test Author 1",
        )
        user1 = sample_user()
        user2 = sample_user(
            email="user2@email.com",
            password="pass2",
        )
        tomorrow = timezone.localdate() + timedelta(days=1)
        Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=tomorrow,
            book=book_1,
            user=user1,
        )
        Borrowing.objects.create(
            borrow_date=timezone.localdate(),
            expected_return_date=tomorrow,
            book=book_2,
            user=user2,
        )

        response = self.client.get(BORROWINGS_LIST_URL, {"user_id": user1.id})
        return_ids = [item["user"] for item in response.data["results"]]
        self.assertIn(user1.id, return_ids)
        self.assertNotIn(user2.id, return_ids)
