from django.db import models
from django.utils import timezone
import uuid
from cloudinary.models import CloudinaryField

# Create your models here.

TEAM_COLORS = [
    ("red", "Red"),
    ("blue", "Blue"),
    ("green", "Green"),
    ("yellow", "Yellow"),
    ("black", "Black"),
    ("white", "White"),
    ("purple", "Purple"),
    ("orange", "Orange"),
]

class Page(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class Volunteerapplication(models.Model):
    volunteer_firstname = models.CharField(max_length=25)
    volunteer_lastname = models.CharField(max_length=25)
    volunteer_email = models.EmailField(unique=False)
    volunteer_phone = models.CharField(max_length=25)
    volunteer_age = models.PositiveIntegerField(null=True, blank=True)
    volunteer_role = models.CharField(max_length=50)
    why_interested = models.TextField()

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.volunteer_firstname} {self.volunteer_lastname}"
    

class Team(models.Model):
    team_name = models.CharField(max_length=100)
    # ✅ NEW: slot locking (1–8)
    slot_number = models.IntegerField(null=True, blank=True)
    captain_name = models.CharField(max_length=100)
    captain_email = models.EmailField(unique=True)
    captain_phone = models.CharField(max_length=25)
    
    waiver_agreed = models.BooleanField(default=False)
    waiver_timestamp = models.DateTimeField(null=True, blank=True)
    player_count = models.IntegerField(default=6)


    created_at = models.DateTimeField(auto_now_add=True)

    team_color = models.CharField(
        max_length=20,
        choices=TEAM_COLORS,
        unique=True
    )   

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS,
        default="pending"
    )
    
    spectator_range = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.team_name
    
class Player(models.Model):
    team = models.ForeignKey(
        "Team",
        on_delete=models.CASCADE,
        related_name="players"
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    age = models.PositiveIntegerField()

    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("N", "Prefer not to say"),
    ]

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES
    )

    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)

    school = models.CharField(max_length=100, blank=True)

    is_substitute = models.BooleanField(default=False)

    # Optional future stats (safe to keep)
    games = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    aces = models.IntegerField(default=0)
    blocks = models.IntegerField(default=0)
    fouls = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.team.team_name})"

class Registration(models.Model):
    team = models.OneToOneField(
        Team,
        on_delete=models.CASCADE,
        related_name="registration"
    )

    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team.team_name} Registration"
    

class Bracket(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Match(models.Model):

    class Meta:
        verbose_name_plural = "Matches"

    ROUND_CHOICES = [
        ("pool", "Pool Play"),
        ("quarter", "Quarter Final"),
        ("semi", "Semi Final"),
        ("final", "Final"),
    ]

    team_1 = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="home_matches"
    )

    team_2 = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="away_matches"
    )

    bracket = models.ForeignKey(
        Bracket,
        on_delete=models.CASCADE,
        related_name="matches"
    )

    round_name = models.CharField(
        max_length=20,
        choices=ROUND_CHOICES,
        default="pool"
    )

    team_1_score = models.IntegerField(default=0)
    team_2_score = models.IntegerField(default=0)

    is_live = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)

    winner = models.ForeignKey(
        Team,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wins"
    )

    match_time = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team_1} vs {self.team_2}"

class FreeAgent(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("in_progress", "In Progress"),
        ("filled", "Filled"),
    ]

    TYPE_CHOICES = [
        ("solo", "Solo Player"),
        ("group", "Group Looking"),
    ]

    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    player_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    instagram = models.CharField(max_length=50)
    note = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    edit_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_new(self):
        return (timezone.now() - self.created_at).days < 1
    
class Creator(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    instagram = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    profile_image = CloudinaryField('image')
    
    def __str__(self):
        return self.name


class Contact(models.Model):
    first_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    source = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class MediaItem(models.Model):

    CATEGORY_CHOICES = [
        ('2024', '2024 Basketball'),
        ('2026', '2026 Volleyball'),
        ('bts', 'Behind The Scenes'),
        ('creative', 'Creative Showcase'),
    ]

    MEDIA_TYPE = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    creator = models.ForeignKey(Creator, on_delete=models.CASCADE)

    title = models.CharField(max_length=200, blank=True)

    media_file = CloudinaryField(
        resource_type='auto'
    )

    thumbnail = CloudinaryField(
        'image',
        blank=True,
        null=True
    )

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE)

    featured = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)