from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from theatre.models import Genre, Actor, Play, TheatreHall, Performance, Reservation, Ticket

User = get_user_model()

GENRES = ["Drama", "Comedy", "Musical", "Thriller", "Tragedy", "Romance"]

ACTORS = [
    ("William", "Shakespeare"),
    ("Meryl", "Streep"),
    ("Ian", "McKellen"),
    ("Judi", "Dench"),
    ("Cate", "Blanchett"),
    ("Ralph", "Fiennes"),
    ("Helen", "Mirren"),
    ("Benedict", "Cumberbatch"),
]

HALLS = [
    ("Grand Hall", 20, 30),
    ("Studio Theatre", 8, 15),
    ("Main Stage", 15, 25),
]

PLAYS = [
    {
        "title": "Hamlet",
        "description": (
            "The Tragedy of Hamlet, Prince of Denmark. A young prince "
            "uncovers the truth about his father's death and struggles "
            "with duty, morality, and revenge."
        ),
        "genres": ["Drama", "Tragedy"],
        "actors": ["William Shakespeare", "Ian McKellen", "Benedict Cumberbatch"],
    },
    {
        "title": "A Midsummer Night's Dream",
        "description": (
            "A comedic tale of love, magic, and mischief set in an "
            "enchanted forest where fairies meddle in human affairs."
        ),
        "genres": ["Comedy", "Romance"],
        "actors": ["Judi Dench", "Helen Mirren"],
    },
    {
        "title": "The Phantom of the Opera",
        "description": (
            "A mysterious masked figure haunts the Paris Opera House "
            "and becomes obsessed with a talented young soprano."
        ),
        "genres": ["Musical", "Drama", "Romance"],
        "actors": ["Ralph Fiennes", "Cate Blanchett"],
    },
    {
        "title": "Macbeth",
        "description": (
            "A Scottish general receives a prophecy that he will become "
            "king, and his ambition — fuelled by his wife — leads to "
            "treachery and madness."
        ),
        "genres": ["Drama", "Tragedy", "Thriller"],
        "actors": ["Ian McKellen", "Judi Dench", "Ralph Fiennes"],
    },
    {
        "title": "The Importance of Being Earnest",
        "description": (
            "Oscar Wilde's comedic masterpiece about mistaken identity, "
            "social satire, and the trivial matters of Victorian society."
        ),
        "genres": ["Comedy"],
        "actors": ["Meryl Streep", "Cate Blanchett", "Benedict Cumberbatch"],
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample data for demo purposes."  # noqa: VNE003

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing theatre data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Flushing existing theatre data...")
            Ticket.objects.all().delete()
            Reservation.objects.all().delete()
            Performance.objects.all().delete()
            Play.objects.all().delete()
            Actor.objects.all().delete()
            Genre.objects.all().delete()
            TheatreHall.objects.all().delete()

        # Genres
        genre_map = {}
        for name in GENRES:
            genre, _ = Genre.objects.get_or_create(name=name)
            genre_map[name] = genre
        self.stdout.write(f"  Genres: {len(genre_map)}")

        # Actors
        actor_map = {}
        for first, last in ACTORS:
            actor, _ = Actor.objects.get_or_create(first_name=first, last_name=last)
            actor_map[f"{first} {last}"] = actor
        self.stdout.write(f"  Actors: {len(actor_map)}")

        # Theatre Halls
        hall_map = {}
        for name, rows, seats in HALLS:
            hall, _ = TheatreHall.objects.get_or_create(
                name=name, defaults={"rows": rows, "seats_in_row": seats}
            )
            hall_map[name] = hall
        self.stdout.write(f"  Halls:  {len(hall_map)}")

        # Plays
        play_map = {}
        for data in PLAYS:
            play, created = Play.objects.get_or_create(
                title=data["title"],
                defaults={"description": data["description"]},
            )
            if created:
                play.genres.set([genre_map[g] for g in data["genres"]])
                play.actors.set([actor_map[a] for a in data["actors"]])
            play_map[data["title"]] = play
        self.stdout.write(f"  Plays:  {len(play_map)}")

        # Performances — spread over the next 14 days
        halls = list(hall_map.values())
        plays = list(play_map.values())
        now = datetime.now(tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        performances = []
        for day_offset in range(1, 15):
            date = now + timedelta(days=day_offset)
            for i, play in enumerate(plays):
                hall = halls[i % len(halls)]
                show_time = date.replace(hour=19, minute=0)
                perf, _ = Performance.objects.get_or_create(
                    play=play, theatre_hall=hall, show_time=show_time,
                )
                performances.append(perf)
        self.stdout.write(f"  Performances: {len(performances)}")

        # Demo user + reservation
        demo_email = "demo@theatre.com"
        demo_user, created = User.objects.get_or_create(
            email=demo_email,
            defaults={"is_staff": False},
        )
        if created:
            demo_user.set_password("demo12345")
            demo_user.save()
            self.stdout.write(
                f"  Demo user created: {demo_email} / demo12345"
            )
        else:
            self.stdout.write(f"  Demo user exists:  {demo_email}")

        # Create a sample reservation on the first performance
        first_perf = performances[0]
        if not Reservation.objects.filter(user=demo_user).exists():
            reservation = Reservation.objects.create(user=demo_user)
            seats = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]
            for row, seat in seats:
                Ticket.objects.create(
                    row=row, seat=seat,
                    performance=first_perf, reservation=reservation,
                )
            self.stdout.write(
                f"  Reservation #{reservation.id}: "
                f"{len(seats)} tickets for {first_perf}"
            )

        self.stdout.write(self.style.SUCCESS("Seed complete."))
