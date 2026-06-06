from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from books.models import Book
from books.serializers import BookSerializer

BOOK_LIST_URL = reverse("books:book-list")


def detail_url(book_id):
    return reverse("books:book-detail", args=[book_id])


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


class BookUnauthenticatedViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_view(self):
        sample_book()
        sample_book(
            title="Sample Book 2",
            author="Test Author",
        )

        response = self.client.get(BOOK_LIST_URL)

        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], serializer.data)

    def test_detail_view(self):
        book = sample_book()

        response = self.client.get(detail_url(book.id))
        serializer = BookSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class BookAdminViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@admin.com",
            password="123",
            is_staff=True,
        )
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        payload = {
            "title": "Sample Book",
            "author": "Test Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": 2.50
        }

        response = self.client.post(BOOK_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Sample Book")
        self.assertEqual(response.data["author"], "Test Author")

    def test_create_book_with_negative_daily_fee(self):
        payload = {
            "title": "Sample Book",
            "author": "Test Author",
            "cover": "SOFT",
            "inventory": 10,
            "daily_fee": -2.50
        }

        response = self.client.post(BOOK_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_book_with_negative_inventory(self):
        payload = {
            "title": "Sample Book",
            "author": "Test Author",
            "cover": "SOFT",
            "inventory": -10,
            "daily_fee": 2.50
        }

        response = self.client.post(BOOK_LIST_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_book(self):
        book = sample_book()
        payload = {
            "title": "Updated Book",
            "author": "Test Author 1",
        }

        response = self.client.patch(detail_url(book.id), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Book")
        self.assertEqual(response.data["author"], "Test Author 1")

    def test_delete_book(self):
        book = sample_book()

        response = self.client.delete(detail_url(book.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
