from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Genre
from theatre.serializers import GenreSerializer

GENRE_URL = reverse("theatre:genre-list")


def detail_url(genre_id):
    return reverse("theatre:genre-detail", args=[genre_id])


class AnonymousGenreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_genres(self):
        Genre.objects.create(name="Drama")
        Genre.objects.create(name="Comedy")

        res = self.client.get(GENRE_URL)

        genres = Genre.objects.all()
        serializer = GenreSerializer(genres, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_genre(self):
        genre = Genre.objects.create(name="Musical")

        res = self.client.get(detail_url(genre.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Musical")

    def test_create_genre_forbidden(self):
        res = self.client.post(GENRE_URL, {"name": "Thriller"})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedGenreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com", "testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_list_genres(self):
        Genre.objects.create(name="Drama")

        res = self.client.get(GENRE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_genre_forbidden(self):
        res = self.client.post(GENRE_URL, {"name": "Thriller"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_genre_forbidden(self):
        genre = Genre.objects.create(name="Drama")

        res = self.client.put(detail_url(genre.id), {"name": "Comedy"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_genre_forbidden(self):
        genre = Genre.objects.create(name="Drama")

        res = self.client.delete(detail_url(genre.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminGenreApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com", "testpass123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_genre(self):
        res = self.client.post(GENRE_URL, {"name": "Drama"})

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Genre.objects.filter(name="Drama").exists())

    def test_create_genre_duplicate_name(self):
        Genre.objects.create(name="Drama")

        res = self.client.post(GENRE_URL, {"name": "Drama"})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_genre(self):
        genre = Genre.objects.create(name="Drama")

        res = self.client.put(detail_url(genre.id), {"name": "Comedy"})

        genre.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(genre.name, "Comedy")

    def test_delete_genre(self):
        genre = Genre.objects.create(name="Drama")

        res = self.client.delete(detail_url(genre.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Genre.objects.filter(id=genre.id).exists())
