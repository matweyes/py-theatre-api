from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Play, Genre, Actor
from theatre.serializers import PlayListSerializer, PlayDetailSerializer

PLAY_URL = reverse("theatre:play-list")


def detail_url(play_id):
    return reverse("theatre:play-detail", args=[play_id])


def sample_play(**params):
    defaults = {
        "title": "Sample Play",
        "description": "Sample description",
    }
    defaults.update(params)
    return Play.objects.create(**defaults)


class AnonymousPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_plays(self):
        sample_play(title="Hamlet")
        sample_play(title="Othello")

        res = self.client.get(PLAY_URL)

        plays = Play.objects.all()
        serializer = PlayListSerializer(plays, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_play_detail(self):
        play = sample_play()
        genre = Genre.objects.create(name="Drama")
        actor = Actor.objects.create(first_name="John", last_name="Doe")
        play.genres.add(genre)
        play.actors.add(actor)

        res = self.client.get(detail_url(play.id))

        serializer = PlayDetailSerializer(play)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_play_forbidden(self):
        res = self.client.post(PLAY_URL, {"title": "Play", "description": "Desc"})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com", "testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_list_plays(self):
        sample_play()

        res = self.client.get(PLAY_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_filter_plays_by_title(self):
        play1 = sample_play(title="Hamlet")
        play2 = sample_play(title="The Hamlet Returns")
        sample_play(title="Othello")

        res = self.client.get(PLAY_URL, {"title": "hamlet"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertEqual(len(res.data), 2)

    def test_filter_plays_by_genre_name(self):
        genre1 = Genre.objects.create(name="Drama")
        genre2 = Genre.objects.create(name="Comedy")

        play1 = sample_play(title="Play 1")
        play2 = sample_play(title="Play 2")
        play1.genres.add(genre1)
        play2.genres.add(genre2)

        sample_play(title="Play without genre")

        res = self.client.get(PLAY_URL, {"genre": "drama"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_filter_plays_by_actor_name(self):
        actor1 = Actor.objects.create(first_name="John", last_name="Doe")
        actor2 = Actor.objects.create(first_name="Jane", last_name="Smith")

        play1 = sample_play(title="Play 1")
        play2 = sample_play(title="Play 2")
        play1.actors.add(actor1)
        play2.actors.add(actor2)

        sample_play(title="Play without actor")

        res = self.client.get(PLAY_URL, {"actor": "doe"})

        serializer1 = PlayListSerializer(play1)
        serializer2 = PlayListSerializer(play2)
        serializer3 = PlayListSerializer(Play.objects.get(title="Play without actor"))

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_create_play_forbidden(self):
        res = self.client.post(PLAY_URL, {"title": "Play", "description": "Desc"})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPlayApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com", "testpass123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_play(self):
        payload = {"title": "Hamlet", "description": "A tragedy by Shakespeare"}
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        self.assertEqual(play.title, payload["title"])
        self.assertEqual(play.description, payload["description"])

    def test_create_play_with_genres(self):
        genre1 = Genre.objects.create(name="Drama")
        genre2 = Genre.objects.create(name="Tragedy")
        payload = {
            "title": "Hamlet",
            "description": "A tragedy",
            "genres": [genre1.id, genre2.id],
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        self.assertEqual(play.genres.count(), 2)

    def test_create_play_with_actors(self):
        actor1 = Actor.objects.create(first_name="Tom", last_name="Hardy")
        actor2 = Actor.objects.create(first_name="Emma", last_name="Stone")
        payload = {
            "title": "New Play",
            "description": "A new play",
            "actors": [actor1.id, actor2.id],
        }
        res = self.client.post(PLAY_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        play = Play.objects.get(id=res.data["id"])
        self.assertEqual(play.actors.count(), 2)

    def test_update_play(self):
        play = sample_play()

        res = self.client.put(detail_url(play.id), {"title": "Updated", "description": "Updated desc"})

        play.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(play.title, "Updated")

    def test_delete_play(self):
        play = sample_play()

        res = self.client.delete(detail_url(play.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Play.objects.filter(id=play.id).exists())
