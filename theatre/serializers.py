from rest_framework import serializers

from theatre.models import Genre, Actor, Play, TheatreHall, Performance


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class PlaySerializer(serializers.ModelSerializer):
    """Base serializer for creating/updating plays."""

    class Meta:
        model = Play
        fields = ("id", "title", "description", "genres", "actors")


class PlayListSerializer(PlaySerializer):
    """Serializer for listing plays with flat related fields."""

    genres = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    actors = serializers.SlugRelatedField(many=True, read_only=True, slug_field="full_name")

    class Meta:
        model = Play
        fields = ("id", "title", "genres", "actors")


class PlayDetailSerializer(PlaySerializer):
    """Serializer for play detail with nested related objects."""

    genres = GenreSerializer(many=True, read_only=True)
    actors = ActorSerializer(many=True, read_only=True)

    class Meta:
        model = Play
        fields = ("id", "title", "description", "genres", "actors")


class TheatreHallSerializer(serializers.ModelSerializer):
    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class PerformanceSerializer(serializers.ModelSerializer):
    """Base serializer for creating/updating performances."""

    class Meta:
        model = Performance
        fields = ("id", "show_time", "play", "theatre_hall")


class PerformanceListSerializer(PerformanceSerializer):
    """Serializer for listing performances with readable names."""

    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(source="theatre_hall.name", read_only=True)
    theatre_hall_capacity = serializers.IntegerField(source="theatre_hall.capacity", read_only=True)

    class Meta:
        model = Performance
        fields = ("id", "show_time", "play_title", "theatre_hall_name", "theatre_hall_capacity")


class PerformanceDetailSerializer(PerformanceSerializer):
    """Serializer for performance detail with nested objects."""

    play = PlayListSerializer(many=False, read_only=True)
    theatre_hall = TheatreHallSerializer(many=False, read_only=True)

    class Meta:
        model = Performance
        fields = ("id", "show_time", "play", "theatre_hall")
