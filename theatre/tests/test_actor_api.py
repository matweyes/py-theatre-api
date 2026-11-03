from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Actor
from theatre.serializers import ActorSerializer

ACTOR_URL = reverse("theatre:actor-list")


def detail_url(actor_id):
    return reverse("theatre:actor-detail", args=[actor_id])


class AnonymousActorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_actors(self):
        Actor.objects.create(first_name="John", last_name="Doe")
        Actor.objects.create(first_name="Jane", last_name="Smith")

        res = self.client.get(ACTOR_URL)

        actors = Actor.objects.all()
        serializer = ActorSerializer(actors, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_actor(self):
        actor = Actor.objects.create(first_name="John", last_name="Doe")

        res = self.client.get(detail_url(actor.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["full_name"], "John Doe")

    def test_create_actor_forbidden(self):
        res = self.client.post(ACTOR_URL, {"first_name": "John", "last_name": "Doe"})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedActorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com", "testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_list_actors(self):
        Actor.objects.create(first_name="John", last_name="Doe")

        res = self.client.get(ACTOR_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_actor_forbidden(self):
        res = self.client.post(ACTOR_URL, {"first_name": "John", "last_name": "Doe"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_actor_forbidden(self):
        actor = Actor.objects.create(first_name="John", last_name="Doe")

        res = self.client.put(detail_url(actor.id), {"first_name": "Jane", "last_name": "Doe"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_actor_forbidden(self):
        actor = Actor.objects.create(first_name="John", last_name="Doe")

        res = self.client.delete(detail_url(actor.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminActorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com", "testpass123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_actor(self):
        res = self.client.post(ACTOR_URL, {"first_name": "John", "last_name": "Doe"})

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Actor.objects.filter(first_name="John", last_name="Doe").exists())

    def test_update_actor(self):
        actor = Actor.objects.create(first_name="John", last_name="Doe")

        res = self.client.put(detail_url(actor.id), {"first_name": "Jane", "last_name": "Smith"})

        actor.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(actor.first_name, "Jane")
        self.assertEqual(actor.last_name, "Smith")

    def test_delete_actor(self):
        actor = Actor.objects.create(first_name="John", last_name="Doe")

        res = self.client.delete(detail_url(actor.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Actor.objects.filter(id=actor.id).exists())
