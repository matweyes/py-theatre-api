from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from theatre.models import Play, TheatreHall, Performance, Reservation, Ticket

TICKET_URL = reverse("theatre:ticket-list")


def detail_url(ticket_id):
    return reverse("theatre:ticket-detail", args=[ticket_id])


def sample_performance(**params):
    defaults = {
        "play": Play.objects.create(title="Test Play", description="Test"),
        "theatre_hall": TheatreHall.objects.create(name="Hall", rows=10, seats_in_row=20),
        "show_time": "2026-09-15 19:00:00",
    }
    defaults.update(params)
    return Performance.objects.create(**defaults)


class AnonymousTicketApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_tickets_forbidden(self):
        res = self.client.get(TICKET_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_ticket_forbidden(self):
        perf = sample_performance()
        user = get_user_model().objects.create_user("u@test.com", "testpass123")
        reservation = Reservation.objects.create(user=user)
        ticket = Ticket.objects.create(row=1, seat=1, performance=perf, reservation=reservation)

        res = self.client.get(detail_url(ticket.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTicketApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("user@test.com", "testpass123")
        self.client.force_authenticate(self.user)
        self.performance = sample_performance()

    def test_list_own_tickets(self):
        reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(row=1, seat=1, performance=self.performance, reservation=reservation)
        Ticket.objects.create(row=1, seat=2, performance=self.performance, reservation=reservation)

        other_user = get_user_model().objects.create_user("other@test.com", "testpass123")
        other_reservation = Reservation.objects.create(user=other_user)
        Ticket.objects.create(row=2, seat=1, performance=self.performance, reservation=other_reservation)

        res = self.client.get(TICKET_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 2)

    def test_retrieve_own_ticket(self):
        reservation = Reservation.objects.create(user=self.user)
        ticket = Ticket.objects.create(row=3, seat=5, performance=self.performance, reservation=reservation)

        res = self.client.get(detail_url(ticket.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["row"], 3)
        self.assertEqual(res.data["seat"], 5)
        self.assertIn("performance", res.data)

    def test_retrieve_other_user_ticket_not_found(self):
        other_user = get_user_model().objects.create_user("other@test.com", "testpass123")
        other_reservation = Reservation.objects.create(user=other_user)
        ticket = Ticket.objects.create(row=1, seat=1, performance=self.performance, reservation=other_reservation)

        res = self.client.get(detail_url(ticket.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_ticket_not_allowed(self):
        res = self.client.post(TICKET_URL, {"row": 1, "seat": 1, "performance": self.performance.id})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_ticket_not_allowed(self):
        reservation = Reservation.objects.create(user=self.user)
        ticket = Ticket.objects.create(row=1, seat=1, performance=self.performance, reservation=reservation)

        res = self.client.delete(detail_url(ticket.id))

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AdminTicketApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            "admin@test.com", "testpass123", is_staff=True
        )
        self.client.force_authenticate(self.admin)
        self.performance = sample_performance()

    def test_list_all_tickets(self):
        user1 = get_user_model().objects.create_user("u1@test.com", "testpass123")
        user2 = get_user_model().objects.create_user("u2@test.com", "testpass123")

        res1 = Reservation.objects.create(user=user1)
        res2 = Reservation.objects.create(user=user2)

        Ticket.objects.create(row=1, seat=1, performance=self.performance, reservation=res1)
        Ticket.objects.create(row=1, seat=2, performance=self.performance, reservation=res2)
        Ticket.objects.create(row=2, seat=1, performance=self.performance, reservation=res2)

        res = self.client.get(TICKET_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 3)

    def test_retrieve_any_ticket(self):
        user = get_user_model().objects.create_user("u@test.com", "testpass123")
        reservation = Reservation.objects.create(user=user)
        ticket = Ticket.objects.create(row=5, seat=10, performance=self.performance, reservation=reservation)

        res = self.client.get(detail_url(ticket.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["row"], 5)
        self.assertEqual(res.data["seat"], 10)
