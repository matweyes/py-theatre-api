from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import TheatreHall
from theatre.serializers import TheatreHallSerializer

THEATRE_HALL_URL = reverse("theatre:theatrehall-list")


def detail_url(hall_id):
    return reverse("theatre:theatrehall-detail", args=[hall_id])


class AnonymousTheatreHallApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_halls(self):
        TheatreHall.objects.create(name="Main", rows=20, seats_in_row=30)
        TheatreHall.objects.create(name="Small", rows=10, seats_in_row=15)

        res = self.client.get(THEATRE_HALL_URL)

        halls = TheatreHall.objects.all()
        serializer = TheatreHallSerializer(halls, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_hall(self):
        hall = TheatreHall.objects.create(name="Main", rows=20, seats_in_row=30)

        res = self.client.get(detail_url(hall.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["name"], "Main")
        self.assertEqual(res.data["capacity"], 600)

    def test_create_hall_forbidden(self):
        res = self.client.post(THEATRE_HALL_URL, {"name": "Hall", "rows": 10, "seats_in_row": 20})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTheatreHallApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@test.com", "testpass123"
        )
        self.client.force_authenticate(self.user)

    def test_list_halls(self):
        TheatreHall.objects.create(name="Main", rows=20, seats_in_row=30)

        res = self.client.get(THEATRE_HALL_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_hall_forbidden(self):
        res = self.client.post(THEATRE_HALL_URL, {"name": "Hall", "rows": 10, "seats_in_row": 20})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_hall_forbidden(self):
        hall = TheatreHall.objects.create(name="Main", rows=20, seats_in_row=30)

        res = self.client.put(detail_url(hall.id), {"name": "Updated", "rows": 25, "seats_in_row": 35})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_hall_forbidden(self):
        hall = TheatreHall.objects.create(name="Main", rows=20, seats_in_row=30)

        res = self.client.delete(detail_url(hall.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTheatreHallApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@test.com", "testpass123", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_hall(self):
        payload = {"name": "Grand Hall", "rows": 25, "seats_in_row": 40}
        res = self.client.post(THEATRE_HALL_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        hall = TheatreHall.objects.get(id=res.data["id"])
        self.assertEqual(hall.name, "Grand Hall")
        self.assertEqual(hall.capacity, 1000)

    def test_update_hall(self):
        hall = TheatreHall.objects.create(name="Main", rows=20, seats_in_row=30)

        res = self.client.put(detail_url(hall.id), {"name": "Updated", "rows": 25, "seats_in_row": 35})

        hall.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(hall.name, "Updated")
        self.assertEqual(hall.rows, 25)
        self.assertEqual(hall.seats_in_row, 35)

    def test_create_hall_invalid_rows(self):
        res = self.client.post(THEATRE_HALL_URL, {"name": "Bad", "rows": 0, "seats_in_row": 10})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_hall_invalid_seats_in_row(self):
        res = self.client.post(THEATRE_HALL_URL, {"name": "Bad", "rows": 10, "seats_in_row": -1})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_hall(self):
        hall = TheatreHall.objects.create(name="Main", rows=20, seats_in_row=30)

        res = self.client.delete(detail_url(hall.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TheatreHall.objects.filter(id=hall.id).exists())
