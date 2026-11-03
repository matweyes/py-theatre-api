from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Play, TheatreHall, Performance, Reservation, Ticket

RESERVATION_URL = reverse("theatre:reservation-list")


def detail_url(reservation_id):
    return reverse("theatre:reservation-detail", args=[reservation_id])


def seats_url(performance_id):
    return reverse("theatre:performance-seats", args=[performance_id])


def sample_performance(**params):
    defaults = {
        "play": Play.objects.create(title="Test Play", description="Test"),
        "theatre_hall": TheatreHall.objects.create(name="Hall", rows=10, seats_in_row=20),
        "show_time": datetime(2026, 9, 15, 19, 0, tzinfo=timezone.utc),
    }
    defaults.update(params)
    return Performance.objects.create(**defaults)


class AnonymousReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_reservations_forbidden(self):
        res = self.client.get(RESERVATION_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_reservation_forbidden(self):
        perf = sample_performance()
        payload = {"tickets": [{"row": 1, "seat": 1, "performance": perf.id}]}

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AnonymousSeatsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_seats_accessible_anonymously(self):
        perf = sample_performance()

        res = self.client.get(seats_url(perf.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["rows"], 10)
        self.assertEqual(res.data["seats_in_row"], 20)
        self.assertEqual(res.data["taken"], [])
        self.assertEqual(len(res.data["available"]), 10 * 20)


class AuthenticatedReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("user@test.com", "testpass123")
        self.client.force_authenticate(self.user)
        self.performance = sample_performance()

    def test_create_reservation(self):
        payload = {
            "tickets": [
                {"row": 1, "seat": 1, "performance": self.performance.id},
                {"row": 1, "seat": 2, "performance": self.performance.id},
            ]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        reservation = Reservation.objects.get(id=res.data["id"])
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.tickets.count(), 2)

    def test_create_reservation_empty_tickets_rejected(self):
        payload = {"tickets": []}

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_invalid_row(self):
        payload = {
            "tickets": [{"row": 99, "seat": 1, "performance": self.performance.id}]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_invalid_seat(self):
        payload = {
            "tickets": [{"row": 1, "seat": 99, "performance": self.performance.id}]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_duplicate_seat_rejected(self):
        Ticket.objects.create(
            row=1, seat=1, performance=self.performance,
            reservation=Reservation.objects.create(user=self.user),
        )
        payload = {
            "tickets": [{"row": 1, "seat": 1, "performance": self.performance.id}]
        }

        res = self.client.post(RESERVATION_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_own_reservations_only(self):
        other_user = get_user_model().objects.create_user("other@test.com", "testpass123")
        Reservation.objects.create(user=self.user)
        Reservation.objects.create(user=other_user)

        res = self.client.get(RESERVATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)

    def test_retrieve_own_reservation(self):
        reservation = Reservation.objects.create(user=self.user)

        res = self.client.get(detail_url(reservation.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], reservation.id)

    def test_retrieve_other_user_reservation_forbidden(self):
        other_user = get_user_model().objects.create_user("other@test.com", "testpass123")
        reservation = Reservation.objects.create(user=other_user)

        res = self.client.get(detail_url(reservation.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_reservation(self):
        reservation = Reservation.objects.create(user=self.user)

        res = self.client.delete(detail_url(reservation.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Reservation.objects.filter(id=reservation.id).exists())

    def test_update_reservation_not_allowed(self):
        reservation = Reservation.objects.create(user=self.user)

        res = self.client.put(detail_url(reservation.id), {"tickets": []}, format="json")

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_seats_shows_taken_and_available(self):
        reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(row=1, seat=1, performance=self.performance, reservation=reservation)
        Ticket.objects.create(row=2, seat=5, performance=self.performance, reservation=reservation)

        res = self.client.get(seats_url(self.performance.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["rows"], 10)
        self.assertEqual(res.data["seats_in_row"], 20)
        self.assertEqual(len(res.data["taken"]), 2)
        taken = [(s["row"], s["seat"]) for s in res.data["taken"]]
        self.assertIn((1, 1), taken)
        self.assertIn((2, 5), taken)
        self.assertEqual(len(res.data["available"]), 10 * 20 - 2)
        available = [(s["row"], s["seat"]) for s in res.data["available"]]
        self.assertNotIn((1, 1), available)
        self.assertNotIn((2, 5), available)


class AdminReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            "admin@test.com", "testpass123", is_staff=True
        )
        self.client.force_authenticate(self.admin)

    def test_list_all_reservations(self):
        user1 = get_user_model().objects.create_user("u1@test.com", "testpass123")
        user2 = get_user_model().objects.create_user("u2@test.com", "testpass123")
        Reservation.objects.create(user=user1)
        Reservation.objects.create(user=user2)
        Reservation.objects.create(user=self.admin)

        res = self.client.get(RESERVATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 3)

    def test_delete_any_reservation(self):
        user = get_user_model().objects.create_user("user@test.com", "testpass123")
        reservation = Reservation.objects.create(user=user)

        res = self.client.delete(detail_url(reservation.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
