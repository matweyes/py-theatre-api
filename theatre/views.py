from datetime import datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from theatre.models import Genre, Actor, Play, TheatreHall, Performance
from theatre.permissions import IsAdminOrReadOnly
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
