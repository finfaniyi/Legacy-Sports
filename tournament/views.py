from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Team, Player, Volunteerapplication, TEAM_COLORS
from django.core.mail import send_mail
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt


# Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# =========================
# PUBLIC PAGES
# =========================

def team_list(request):
    teams = Team.objects.filter(
        payment_status="paid"
    ).order_by("slot_number")

    return render(request, "tournament/teams.html", {
        "teams": teams
    })


def home(request):
    return render(request, "tournament/index.html")


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
            subject="Legacy Sports Volunteer Application Received ⚡",
            message=f"""
            Hi {first_name},

            Thank you for applying to join Legacy Sports Team.

            Role Applied For: {role}

            We have received your application and will reach out soon.

            — Legacy Sports
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

    return render(request, "tournament/registration_display.html", {
        "taken_slots": taken_slots,
        "slot_colors": slot_colors,
        "slot_names": slot_names,
    })


def registration_success(request):
    return redirect("/registration/?paid=true")

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
    slot = request.GET.get("slot")

    taken_colors = set(
        Team.objects.values_list("team_color", flat=True)
    )

    if request.method == "POST":

        if not request.POST.get("agree_waiver"):
            return render(request, "tournament/registration-form.html", {
                "error": "You must agree to the waiver.",
                "taken_colors": taken_colors,
                "team_colors": TEAM_COLORS,
            })

        team_color = request.POST.get("team_color")

        if Team.objects.filter(slot_number=slot).exists():
            return redirect("/registration/?error=slot_taken")

        if Team.objects.filter(team_color=team_color).exists():
            return render(request, "tournament/registration-form.html", {
                "error": "Color already taken.",
                "taken_colors": taken_colors,
                "team_colors": TEAM_COLORS,
            })

        # Player count logic
        player_count = int(request.POST.get("player_count", 6))

        if player_count < 6:
            player_count = 6
        if player_count > 8:
            player_count = 8

        # TEST PRICE (50 cents per player)
        price_per_player = 50
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
            success_url=request.build_absolute_uri("/registration-success/"),
            cancel_url=request.build_absolute_uri("/registration/?cancelled=true"),
            metadata={
                "slot": slot,
                "team_name": request.POST["team_name"],
                "captain_name": request.POST["captain_name"],
                "captain_email": request.POST["captain_email"],
                "captain_phone": request.POST["captain_phone"],
                "team_color": team_color,
                "player_count": player_count,
            }
        )

        return redirect(checkout_session.url)

    return render(request, "tournament/registration-form.html", {
        "taken_colors": taken_colors,
        "team_colors": TEAM_COLORS,
    })


# =========================
# STRIPE WEBHOOK
# =========================

@csrf_exempt
def stripe_webhook(request):
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
        metadata = session.get("metadata", {})

        slot = metadata.get("slot")
        team_name = metadata.get("team_name")
        captain_name = metadata.get("captain_name")
        captain_email = metadata.get("captain_email")
        captain_phone = metadata.get("captain_phone")
        team_color = metadata.get("team_color")
        player_count = int(metadata.get("player_count", 6))

        if not Team.objects.filter(slot_number=slot).exists():

            Team.objects.create(
                slot_number=slot,
                team_name=team_name,
                captain_name=captain_name,
                captain_email=captain_email,
                captain_phone=captain_phone,
                team_color=team_color,
                player_count=player_count,
                payment_status="paid",
                waiver_agreed=True,
                waiver_timestamp=timezone.now(),
            )

            # Captain confirmation
            send_mail(
                subject="Legacy Sports Team Registration Confirmed ⚡",
                message=f"""
                Hi {captain_name},

                Your team "{team_name}" is officially registered.

                Slot: {slot}
                Team Color: {team_color}
                Players: {player_count}

                — Legacy Sports
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[captain_email],
                fail_silently=False,
            )

            # Admin notification
            send_mail(
                subject="🚨 New Paid Team Registration",
                message=f"""
                Team: {team_name}
                Captain: {captain_name}
                Slot: {slot}
                Players: {player_count}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["legacysportscanada@gmail.com"],
                fail_silently=False,
            )

    return JsonResponse({"status": "success"})
