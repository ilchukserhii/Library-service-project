from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.serializers import UserManageSerializer


class UserModelTest(TestCase):
    def test_user_creation_with_email(self):
        user = get_user_model().objects.create_user(
            email="user@email.com",
            password="password",
        )
        user.refresh_from_db()
        self.assertEqual(user.email, "user@email.com")
        self.assertTrue(user.check_password("password"))
        self.assertIsNone(user.username)


class UserCreateViewTest(TestCase):
    def test_user_create(self):
        payload = {
            "email": "user@user.com",
            "password": "password",
        }

        response = self.client.post(reverse("users:create"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class UserObtainRefreshTokenViewTest(TestCase):
    def test_obtain_user_token(self):
        get_user_model().objects.create_user(
            email="user@user.com",
            password="password",
        )

        payload = {
            "email": "user@user.com",
            "password": "password",
        }

        response = self.client.post(
            reverse("users:token_obtain_pair"),
            payload
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_user_token(self):
        get_user_model().objects.create_user(
            email="user@user.com",
            password="password",
        )

        payload = {
            "email": "user@user.com",
            "password": "password",
        }

        response_obtain = self.client.post(
            reverse("users:token_obtain_pair"),
            payload
        )

        refresh = response_obtain.data["refresh"]

        payload = {
            "refresh": refresh,
        }

        response = self.client.post(
            reverse("users:token_refresh"),
            payload
        )

        self.assertIn("access", response.data)


class UserManageViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@email.com",
            password="password",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_profile(self):
        response = self.client.get(reverse("users:me"))

        serializer = UserManageSerializer(self.user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_update_profile(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
        }

        response = self.client.patch(
            reverse("users:me"),
            payload,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"],  "John")
        self.assertEqual(response.data["last_name"], "Doe")


class UnauthorizedUserManageViewTest(TestCase):
    def test_unauthorized_user_manage_view(self):
        client = APIClient()
        response = client.get(reverse("users:me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
