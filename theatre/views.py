from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets

from theatre.models import Genre, Actor, Play, TheatreHall
from theatre.permissions import IsAdminOrReadOnly
from theatre.serializers import (
    GenreSerializer,
    ActorSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayDetailSerializer,
    TheatreHallSerializer,
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
