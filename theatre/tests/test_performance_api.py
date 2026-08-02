from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Play, TheatreHall, Performance
from theatre.serializers import PerformanceListSerializer, PerformanceDetailSerializer

PERFORMANCE_URL = reverse("theatre:performance-list")


def detail_url(performance_id):
    return reverse("theatre:performance-detail", args=[performance_id])


def sample_play(**params):
    defaults = {"title": "Sample Play", "description": "A sample play"}
    defaults.update(params)
    return Play.objects.create(**defaults)


def sample_hall(**params):
    defaults = {"name": "Main Hall", "rows": 20, "seats_in_row": 30}
    defaults.update(params)
    return TheatreHall.objects.create(**defaults)


def sample_performance(**params):
    defaults = {
        "play": params.pop("play", None) or sample_play(),
        "theatre_hall": params.pop("theatre_hall", None) or sample_hall(),
        "show_time": "2026-09-15 19:00:00",
    }
    defaults.update(params)
    return Performance.objects.create(**defaults)


class AnonymousPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_performances(self):
        sample_performance()
        sample_performance(
            play=sample_play(title="Other"),
            theatre_hall=sample_hall(name="Small"),
            show_time="2026-09-16 20:00:00",
        )

        res = self.client.get(PERFORMANCE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 2)

    def test_list_performances_paginated(self):
        play = sample_play()
        hall = sample_hall()
        for i in range(15):
            Performance.objects.create(
                play=play, theatre_hall=hall, show_time=f"2026-10-{i + 1:02d} 19:00:00"
            )

        res = self.client.get(PERFORMANCE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 15)
        self.assertEqual(len(res.data["results"]), 10)
        self.assertIsNotNone(res.data["next"])

    def test_retrieve_performance_detail(self):
        performance = sample_performance()

        res = self.client.get(detail_url(performance.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("play", res.data)
        self.assertIn("theatre_hall", res.data)
        self.assertIn("title", res.data["play"])
        self.assertIn("capacity", res.data["theatre_hall"])

    def test_create_performance_forbidden(self):
        play = sample_play()
        hall = sample_hall()
        payload = {
            "play": play.id,
            "theatre_hall": hall.id,
            "show_time": "2026-09-20 19:00:00",
        }

        res = self.client.post(PERFORMANCE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("user@test.com", "testpass123")
        self.client.force_authenticate(self.user)

    def test_list_performances(self):
        sample_performance()

        res = self.client.get(PERFORMANCE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_filter_by_play_title(self):
        play1 = sample_play(title="Hamlet")
        play2 = sample_play(title="Othello")
        hall = sample_hall()

        Performance.objects.create(play=play1, theatre_hall=hall, show_time="2026-09-15 19:00:00")
        Performance.objects.create(play=play2, theatre_hall=hall, show_time="2026-09-16 19:00:00")

        res = self.client.get(PERFORMANCE_URL, {"play": "hamlet"})

        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["play_title"], "Hamlet")

    def test_filter_by_date(self):
        play = sample_play()
        hall = sample_hall()

        Performance.objects.create(play=play, theatre_hall=hall, show_time="2026-09-15 19:00:00")
        Performance.objects.create(play=play, theatre_hall=hall, show_time="2026-09-16 20:00:00")

        res = self.client.get(PERFORMANCE_URL, {"date": "2026-09-15"})

        self.assertEqual(res.data["count"], 1)

    def test_filter_by_hall_name(self):
        play = sample_play()
        hall1 = sample_hall(name="Grand Hall")
        hall2 = sample_hall(name="Studio")

        Performance.objects.create(play=play, theatre_hall=hall1, show_time="2026-09-15 19:00:00")
        Performance.objects.create(play=play, theatre_hall=hall2, show_time="2026-09-15 20:00:00")

        res = self.client.get(PERFORMANCE_URL, {"hall": "grand"})

        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["theatre_hall_name"], "Grand Hall")

    def test_create_performance_forbidden(self):
        play = sample_play()
        hall = sample_hall()
        payload = {
            "play": play.id,
            "theatre_hall": hall.id,
            "show_time": "2026-09-20 19:00:00",
        }

        res = self.client.post(PERFORMANCE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminPerformanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com", "testpass123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_performance(self):
        play = sample_play()
        hall = sample_hall()
        payload = {
            "play": play.id,
            "theatre_hall": hall.id,
            "show_time": "2026-09-20 19:00:00",
        }

        res = self.client.post(PERFORMANCE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Performance.objects.filter(id=res.data["id"]).exists())

    def test_update_performance(self):
        performance = sample_performance()
        new_hall = sample_hall(name="Updated Hall")

        res = self.client.patch(detail_url(performance.id), {"theatre_hall": new_hall.id})

        performance.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(performance.theatre_hall.id, new_hall.id)

    def test_delete_performance(self):
        performance = sample_performance()

        res = self.client.delete(detail_url(performance.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Performance.objects.filter(id=performance.id).exists())
