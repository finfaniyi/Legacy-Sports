from django.db import IntegrityError
from datetime import datetime
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Team, Player, Volunteerapplication, TEAM_COLORS
from django.core.mail import send_mail
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import stripe
from .models import Page
from django.views.decorators.csrf import csrf_exempt
import requests
import feedparser
import re
from zoneinfo import ZoneInfo



# Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# =========================
# PUBLIC PAGES
# =========================

def page_detail(request, slug):
    page = Page.objects.get(slug=slug)  # Or use get_object_or_404
    return render(request, 'page_detail.html', {'page': page})

def team_list(request):
    teams = Team.objects.filter(
        payment_status="paid"
    ).order_by("slot_number")

    return render(request, "tournament/teams.html", {
        "teams": teams
    })

def instagram_image_proxy(request):
    image_url = request.GET.get("url")

    if not image_url:
        return HttpResponse(status=400)

    response = requests.get(image_url)

    return HttpResponse(
        response.content,
        content_type=response.headers['Content-Type']
    )

def home(request):
    feed_url = "https://rss.app/feeds/eU7lNyFNqsLEeDg7.xml"
    feed = feedparser.parse(feed_url)

    instagram_posts = []

    for entry in feed.entries[:3]:
        image_url = None

        # 🔥 Use media_content directly
        if "media_content" in entry:
            image_url = entry.media_content[0]["url"]

        instagram_posts.append({
            "image": image_url,
            "link": entry.link,
            "caption": entry.title
        })

    return render(request, "tournament/index.html", {
        "instagram_posts": instagram_posts
    })


def support(request):
    return render(request, "tournament/support.html")


def about(request):
    return render(request, "tournament/about.html")


def history(request):
    return render(request, "tournament/history.html")


def media(request):
    return render(request, "tournament/media.html")


def tourney_info(request):
    return render(request, "tournament/tourney-info.html")


def contact_us(request):
    return render(request, "tournament/contact_us.html")


def team_brackets(request):
    return render(request, "tournament/team_brackets.html")


# =========================
# VOLUNTEER
# =========================

def join_team(request):

    if request.method == "POST":

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        age = request.POST.get("age")
        role = request.POST.get("role_interest")
        experience = request.POST.get("experience")

        missing_fields = []

        if not first_name:
            missing_fields.append("First Name")
        if not last_name:
            missing_fields.append("Last Name")
        if not email:
            missing_fields.append("Email")
        if not phone:
            missing_fields.append("Phone Number")
        if not role:
            missing_fields.append("Role")

        if missing_fields:
            return render(request, "tournament/join_team.html", {
                "error": "Please fill out: " + ", ".join(missing_fields)
            })

        Volunteerapplication.objects.create(
            volunteer_firstname=first_name,
            volunteer_lastname=last_name,
            volunteer_email=email,
            volunteer_phone=phone,
            volunteer_age=age if age else None,
            volunteer_role=role,
            why_interested=experience
        )

        # Confirmation to volunteer
        send_mail(
            subject="📩 Legacy Sports Volunteer Application Received ⚡",
            message=f"""
            
            Hi {first_name},

            Thank you for applying to join Legacy Sports Team.
            We’re excited that you’re interested in being part of what we’re building.
            
            You applied for: {role}

            Our team will be reviewing submissions over the next few days, and we will reach out with next steps shortly.

            What Happens Next:
            • Applicants will be contacted for a brief conversation.
            • Selected volunteers will receive onboarding details and event information.
            • Briefing sessions will be scheduled prior to the tournament.

            We truly appreciate your interest in helping us build something meaningful in the community.

            If you have any questions, feel free to reach out at: 
            
            legacysportscanada@gmail.com
        
            — Legacy Sports Canada
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        # Notify admin
        send_mail(
            subject="🚨 New Volunteer Application - Legacy Sports",
            message=f"""
            New volunteer application received:

            Name: {first_name} {last_name}
            Email: {email}
            Phone: {phone}
            Age: {age}
            Role: {role}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["legacysportscanada@gmail.com"],
            fail_silently=False,
        )

        messages.success(request, "Application submitted successfully!")
        return redirect("join_team")

    return render(request, "tournament/join_team.html")


# =========================
# REGISTRATION DISPLAY
# =========================

def registration(request):
    teams = Team.objects.all()

    taken_slots = set()
    slot_colors = {}
    slot_names = {}

    for team in teams:
        taken_slots.add(team.slot_number)
        slot_colors[team.slot_number] = team.team_color
        slot_names[team.slot_number] = team.team_name

    # 🔥 REGISTRATION WINDOW CONTROL
    toronto = ZoneInfo("America/Toronto")
    now = timezone.now().astimezone(toronto)

    registration_open = datetime( #Year, Month, Day, Time, Minutes, Seconds
        2026, 4, 1, 00, 00, 0,
        tzinfo=toronto
    )

    registration_close = datetime(
        2026, 5, 21, 00, 00, 0,
        tzinfo=toronto
    )

    full = len(taken_slots) >= 8

    return render(request, "tournament/registration_display.html", {
        "taken_slots": taken_slots,
        "slot_colors": slot_colors,
        "slot_names": slot_names,
        "now": now,
        "registration_open": registration_open,
        "registration_close": registration_close,
        "full": full,
    })

def registration_success(request):
    session_id = request.GET.get("session_id")
    if not session_id:
        return redirect("registration")
    return render(request, "tournament/registration_success.html")


def waiver(request):
    next_url = request.GET.get("next", "/")

    if request.method == "POST":
        request.session["waiver_accepted"] = True
        request.session["waiver_timestamp"] = str(timezone.now())
        return redirect(next_url)

    return render(request, "tournament/waiver.html", {
        "next": next_url
    })


# =========================
# TEAM REGISTRATION + STRIPE
# =========================

def registration_team(request):

    slot_value = request.GET.get("slot")
    spectator_range = request.POST.get("spectator_range")

    if not slot_value:
        return redirect("/registration/")

    try:
        slot = int(slot_value)
    except ValueError:
        return redirect("/registration/")

    taken_colors = set(
        Team.objects.values_list("team_color", flat=True)
    )

    if request.method == "POST":

        team_color = request.POST.get("team_color")

        if Team.objects.filter(slot_number=slot).exists():
            return redirect("/registration/?error=slot_taken")

        if Team.objects.filter(team_color=team_color).exists():
            return render(request, "tournament/registration-form.html", {
                "error": "Color already taken.",
                "taken_colors": taken_colors,
                "team_colors": TEAM_COLORS,
            })

        player_count = int(request.POST.get("roster_size", 6))
        player_count = max(6, min(8, player_count))

        captain_email = request.POST.get("captain_email")

        if Team.objects.filter(captain_email=captain_email).exists():
            return render(request, "tournament/registration-form.html", {
                "error_field": "captain_email",
                "error_message": "This email has already registered a team.",
                "taken_colors": taken_colors,
                "team_colors": TEAM_COLORS,
                "slot": slot,
                "form_data": request.POST,
            })

        # CREATE TEAM (PENDING)
        team = Team.objects.create(
            slot_number=slot,
            team_name=request.POST["team_name"],
            captain_name=request.POST["captain_name"],
            captain_email=request.POST["captain_email"],
            captain_phone=request.POST["captain_phone"],
            team_color=team_color,
            player_count=player_count,
            payment_status="pending",
            waiver_agreed=True,
            spectator_range=spectator_range,
            waiver_timestamp=timezone.now(),
        )

        # ACTIVE PLAYERS (1–6)
        for i in range(1, 7):

            age_value = request.POST.get(f"player_{i}_age")

            if not age_value:
                return render(request, "tournament/registration-form.html", {
                    "error": f"Player {i} age is required.",
                    "taken_colors": taken_colors,
                    "team_colors": TEAM_COLORS,
                })

            try:
                age_value = int(age_value)
            except ValueError:
                return render(request, "tournament/registration-form.html", {
                    "error": f"Player {i} age must be a number.",
                    "taken_colors": taken_colors,
                    "team_colors": TEAM_COLORS,
                })

            Player.objects.create(
                team=team,
                first_name=request.POST.get(f"player_{i}_first"),
                last_name=request.POST.get(f"player_{i}_last"),
                age=age_value,
                gender=request.POST.get(f"player_{i}_gender"),
                contact_email=request.POST.get(f"player_{i}_email"),
                contact_phone=request.POST.get(f"player_{i}_phone"),
                school=request.POST.get(f"player_{i}_school") or "",
                is_substitute=False
            )

        # SUBSTITUTE 1
        if player_count >= 7:

            sub1_age = request.POST.get("sub_1_age")

            if not sub1_age:
                return render(request, "tournament/registration-form.html", {
                    "error": "Substitute 1 age is required.",
                    "taken_colors": taken_colors,
                    "team_colors": TEAM_COLORS,
                })

            try:
                sub1_age = int(sub1_age)
            except ValueError:
                return render(request, "tournament/registration-form.html", {
                    "error": "Substitute 1 age must be a number.",
                    "taken_colors": taken_colors,
                    "team_colors": TEAM_COLORS,
                })

            Player.objects.create(
                team=team,
                first_name=request.POST.get("sub_1_first"),
                last_name=request.POST.get("sub_1_last"),
                age=sub1_age,
                gender=request.POST.get("sub_1_gender"),
                contact_email=request.POST.get("sub_1_email"),
                contact_phone=request.POST.get("sub_1_phone"),
                school=request.POST.get("sub_1_school") or "",
                is_substitute=True
            )

        # SUBSTITUTE 2
        if player_count == 8:

            sub2_age = request.POST.get("sub_2_age")

            if not sub2_age:
                return render(request, "tournament/registration-form.html", {
                    "error": "Substitute 2 age is required.",
                    "taken_colors": taken_colors,
                    "team_colors": TEAM_COLORS,
                })

            try:
                sub2_age = int(sub2_age)
            except ValueError:
                return render(request, "tournament/registration-form.html", {
                    "error": "Substitute 2 age must be a number.",
                    "taken_colors": taken_colors,
                    "team_colors": TEAM_COLORS,
                })

            Player.objects.create(
                team=team,
                first_name=request.POST.get("sub_2_first"),
                last_name=request.POST.get("sub_2_last"),
                age=sub2_age,
                gender=request.POST.get("sub_2_gender"),
                contact_email=request.POST.get("sub_2_email"),
                contact_phone=request.POST.get("sub_2_phone"),
                school=request.POST.get("sub_2_school") or "",
                is_substitute=True
            )

        # 💰 Stripe
        price_per_player = 150
        total_amount = player_count * price_per_player

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "cad",
                    "product_data": {
                        "name": f"Legacy Sports Team Entry ({player_count} players)",
                    },
                    "unit_amount": total_amount,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.build_absolute_uri("/registration-success/?session_id={CHECKOUT_SESSION_ID}"),
            cancel_url=request.build_absolute_uri("/registration/?cancelled=true"),
            metadata={
                "team_id": team.id
            }
        )

        return redirect(checkout_session.url)

    return render(request, "tournament/registration-form.html", {
        "taken_colors": taken_colors,
        "team_colors": TEAM_COLORS,
        "slot": slot,
    })



# =========================
# STRIPE WEBHOOK
# =========================

@csrf_exempt
def stripe_webhook(request):
    print("WEBHOOK HIT")
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception:
        return JsonResponse({"error": "Invalid webhook"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.metadata or {}

        team_id = metadata["team_id"] if "team_id" in metadata else None
        
        if not team_id:
            print("❌ Missing team_id in metadata:", metadata)
            return JsonResponse({"error": "Missing team_id"}, status=400)

        if not team_id:
            print("❌ No team_id in metadata")
            return JsonResponse({"error": "Missing team_id"}, status=400)

        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            print(f"❌ Team not found: {team_id}")
            return JsonResponse({"error": "Team not found"}, status=400)

        # ✅ Only runs if valid
        team.payment_status = "paid"
        team.save()

        try:
            team = Team.objects.get(id=team_id)
            team.payment_status = "paid"
            team.save()
        except Team.DoesNotExist:
            return JsonResponse({"error": "Team not found"}, status=400)

        # Player confirmation
        for player in team.players.all():
            if player.contact_email:  # make sure email exists
                send_mail(
                    subject="Legacy Sports Volleyball Tournament Confirmation 🏐⚡",
                    message=f"""
                        Hello,

                        You’ve been registered for the Legacy Sports volleyball tournament!

                        Please complete your waiver form:
                        https://legacysportscanada.ca/waiver
                        """,
                    html_message=f"""
                    <p>Hello,</p>

                    <p>
                    Your team "<strong>{team.team_name}</strong>" is officially registered for the Legacy Sports volleyball tournament!
                    </p>

                    <p>
                    We are excited to have you join us for a fun day of volleyball, teamwork, and meeting new people.
                    </p>

                    <p>
                    Before you arrive, please complete the 
                    <a href="https://legacysportscanada.ca/waiver" target="_blank">
                    waiver form
                    </a> 
                    to help speed up the check-in process. All participants should be ready to show proof of waiver completion, valid ID, and their ticket or registration confirmation at check-in.
                    </p>

                    <p><strong>Team details:</strong></p>
                    <p>
                    • Team name: {team.team_name}<br>
                    • Team Color: {team.team_color}<br>
                    • Total players in your team: {team.player_count}
                    </p>

                    <p><strong>Location:</strong><br>
                    ACE Active Zone, Unit 5, 7093 Torbram Rd, Mississauga, ON
                    </p>

                    <p><strong>Arrival:</strong><br>
                    The tournament begins at 10:30 AM, but we strongly recommend arriving at least 15 minutes early for registration and check-in.
                    </p>

                    <p>
                    Please make sure your full team is checked in before your first game starts. Late arrivals may impact the tournament schedule for everyone.
                    </p>

                    <p>
                    No entry will be permitted after the tournament start time, so please plan accordingly and allow extra time for traffic, parking, and check-in.
                    </p>

                    <p><strong>Parking:</strong><br>
                    There is plenty of free on-site parking available for guests and families.
                    </p>

                    <p><strong>Bleacher seating:</strong><br>
                    Comfortable bleacher seating will be available for supporters to watch the games.
                    </p>

                    <p><strong>Age Requirement:</strong><br>
                    This event is for ages 16 - 25.
                    </p>

                    <strong>What to Bring:</strong>
                    <br>
                    <ul>
                        <li>Valid ID</li>
                        <li>Ticket or registration confirmation</li>
                        <li>Signed waiver</li>
                        <li>Water bottle</li>
                        <li>Athletic clothing in your team’s colour</li>
                        <li>Indoor running shoes</li>
                        <li>Any snacks you may want throughout the day</li>
                    </ul>
                    <p>
                    Got last-minute questions? Email us at legacysportscanada@gmail.com.
                    </p>

                    <p>
                    See you soon!<br><br>
                    Legacy Sports
                    </p>
                    """,
                    
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[player.contact_email],
                    fail_silently=False,
                )

        # Admin notification
        send_mail(
            subject="🚨 New Paid Team Registration",
            message=f"""
            Team: {team.team_name}
            Captain: {team.captain_name}
            Slot: {team.slot_number}
            Players: {team.player_count}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["legacysportscanada@gmail.com"],
            fail_silently=False,
        )

    return JsonResponse({"status": "success"})
