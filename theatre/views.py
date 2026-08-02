from datetime import datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from theatre.models import Genre, Actor, Play, TheatreHall, Performance, Reservation, Ticket
from theatre.permissions import IsAdminOrReadOnly, IsAdminOrOwner
from theatre.serializers import (
    GenreSerializer,
    ActorSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    TheatreHallSerializer,
    PerformanceSerializer,
    PerformanceListSerializer,
    PerformanceDetailSerializer,
    TicketSeatsSerializer,
    TicketListSerializer,
    TicketDetailSerializer,
    ReservationSerializer,
    ReservationListSerializer,
    ReservationDetailSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    permission_classes = (IsAdminOrReadOnly,)


class PlayViewSet(viewsets.ModelViewSet):
    queryset = Play.objects.prefetch_related("genres", "actors")
    serializer_class = PlaySerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        title = self.request.query_params.get("title")
        genre = self.request.query_params.get("genre")
        actor = self.request.query_params.get("actor")

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)

        if genre:
            queryset = queryset.filter(genres__name__icontains=genre)

        if actor:
            queryset = queryset.filter(
                actors__last_name__icontains=actor
            ) | queryset.filter(
                actors__first_name__icontains=actor
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return PlayListSerializer
        if self.action == "retrieve":
            return PlayDetailSerializer
        return PlaySerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "title",
                type=OpenApiTypes.STR,
                description="Filter by play title (ex. ?title=hamlet)",
            ),
            OpenApiParameter(
                "genre",
                type=OpenApiTypes.STR,
                description="Filter by genre name (ex. ?genre=drama)",
            ),
            OpenApiParameter(
                "actor",
                type=OpenApiTypes.STR,
                description="Filter by actor name (ex. ?actor=smith)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TheatreHallViewSet(viewsets.ModelViewSet):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer
    permission_classes = (IsAdminOrReadOnly,)


class PerformancePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.select_related("play", "theatre_hall")
    serializer_class = PerformanceSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = PerformancePagination

    def get_queryset(self):
        play = self.request.query_params.get("play")
        date = self.request.query_params.get("date")
        hall = self.request.query_params.get("hall")

        queryset = self.queryset

        if play:
            queryset = queryset.filter(play__title__icontains=play)

        if date:
            date = datetime.strptime(date, "%Y-%m-%d").date()
            queryset = queryset.filter(show_time__date=date)

        if hall:
            queryset = queryset.filter(theatre_hall__name__icontains=hall)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PerformanceListSerializer
        if self.action == "retrieve":
            return PerformanceDetailSerializer
        if self.action == "seats":
            return TicketSeatsSerializer
        return PerformanceSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "play",
                type=OpenApiTypes.STR,
                description="Filter by play title (ex. ?play=hamlet)",
            ),
            OpenApiParameter(
                "date",
                type=OpenApiTypes.DATE,
                description="Filter by date (ex. ?date=2026-08-15)",
            ),
            OpenApiParameter(
                "hall",
                type=OpenApiTypes.STR,
                description="Filter by theatre hall name (ex. ?hall=grand)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["get"], url_path="seats")
    def seats(self, request, pk=None):
        """Return seat map for this performance."""
        performance = self.get_object()
        hall = performance.theatre_hall
        taken_tickets = Ticket.objects.filter(performance=performance)
        taken = TicketSeatsSerializer(taken_tickets, many=True).data
        taken_set = {(t["row"], t["seat"]) for t in taken}

        available = [
            {"row": r, "seat": s}
            for r in range(1, hall.rows + 1)
            for s in range(1, hall.seats_in_row + 1)
            if (r, s) not in taken_set
        ]

        return Response(
            {
                "rows": hall.rows,
                "seats_in_row": hall.seats_in_row,
                "taken": taken,
                "available": available,
            },
            status=status.HTTP_200_OK,
        )


class ReservationPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Reservation.objects.prefetch_related("tickets__performance__play")
    serializer_class = ReservationSerializer
    permission_classes = (IsAuthenticated, IsAdminOrOwner)
    pagination_class = ReservationPagination

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ReservationListSerializer
        if self.action == "retrieve":
            return ReservationDetailSerializer
        return ReservationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TicketViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Ticket.objects.select_related(
        "performance__play", "performance__theatre_hall", "reservation"
    )
    serializer_class = TicketListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = ReservationPagination

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_staff:
            queryset = queryset.filter(reservation__user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TicketDetailSerializer
        return TicketListSerializer
