from django.db import IntegrityError
from django.shortcuts import render,redirect
from .models import Team,Player
from .models import TEAM_COLORS


# Create your views here.

def team_list(request):
    teams = Team.objects.filter(
        payment_status="paid"
    ).order_by("slot_number")

    return render(request, "tournament/teams.html", {
        "teams": teams
    })

def home(request):
    return render(request, "tournament/index.html")


def about(request):
    return render(request, "tournament/about.html")


def history(request):
    return render(request, "tournament/history.html")


def media(request):
    return render(request, "tournament/media.html")


def registration(request):
    teams = Team.objects.filter(payment_status="paid")

    taken_slots = set()
    slot_colors = {}
    slot_names = {}

    

    for team in teams:
        taken_slots.add(team.slot_number)
        slot_colors[team.slot_number] = team.team_color
        slot_names[team.slot_number] = team.team_name

    is_full = len(taken_slots) >= 8
    
    return render(request, "tournament/registration.html", {
        "taken_slots": taken_slots,
        "slot_colors": slot_colors,
        "slot_names": slot_names,
    })


def registration_success(request):
    return render(request, "tournament/registration_success.html")

def tourney_info(request):
    return render(request, "tournament/tourney-info.html")

def registration_team(request):
    slot = request.GET.get("slot")

    # Colors already taken (used on GET + errors)
    taken_colors = set(
        Team.objects.values_list("team_color", flat=True)
    )

    if request.method == "POST":
        # 🔒 HARD SLOT LOCK
        if Team.objects.filter(slot_number=slot).exists():
            return redirect("/registration/?error=slot_taken")

        team_color = request.POST.get("team_color")

        # 🔒 HARD COLOR LOCK
        if Team.objects.filter(team_color=team_color).exists():
            return render(request, "tournament/registration-team.html", {
                "error": "This color has already been taken.",
                "taken_colors": taken_colors,
                "team_colors": TEAM_COLORS,
            })

        # CREATE TEAM
        team = Team.objects.create(
            slot_number=slot,
            team_name=request.POST["team_name"],
            captain_name=request.POST["captain_name"],
            captain_email=request.POST["captain_email"],
            captain_phone=request.POST["captain_phone"],
            emergency_contact_name=request.POST["team_emergency_name"],
            emergency_contact_phone=request.POST["team_emergency_phone"],
            team_color=team_color,
            payment_status="pending",
        )

        # ACTIVE PLAYERS (6 required)
        for i in range(1, 7):
            Player.objects.create(
                team=team,
                first_name=request.POST[f"player_{i}_first"],
                last_name=request.POST[f"player_{i}_last"],
                age=request.POST[f"player_{i}_age"],
                gender=request.POST[f"player_{i}_gender"],
                contact_email=request.POST[f"player_{i}_email"],
                contact_phone=request.POST[f"player_{i}_phone"],
                emergency_contact_name=request.POST[f"player_{i}_emergency_name"],
                emergency_contact_phone=request.POST[f"player_{i}_emergency_phone"],
                school=request.POST.get(f"player_{i}_school", ""),
                is_substitute=False,
            )

        # SUBSTITUTES (0–2)
        for i in range(1, 3):
            first = request.POST.get(f"sub_{i}_first")
            if not first:
                continue

            Player.objects.create(
                team=team,
                first_name=first,
                last_name=request.POST[f"sub_{i}_last"],
                age=request.POST[f"sub_{i}_age"],
                gender=request.POST[f"sub_{i}_gender"],
                contact_email=request.POST[f"sub_{i}_email"],
                contact_phone=request.POST[f"sub_{i}_phone"],
                emergency_contact_name=request.POST[f"sub_{i}_emergency_name"],
                emergency_contact_phone=request.POST[f"sub_{i}_emergency_phone"],
                school=request.POST.get(f"sub_{i}_school", ""),
                is_substitute=True,
            )
            STRIPE_PAYMENT_LINK = "https://buy.stripe.com/test_0QwdR9690f8YQwdzi8w00"

        return redirect(STRIPE_PAYMENT_LINK)
    
    # GET request
    return render(request, "tournament/registration-team.html", {
        "taken_colors": taken_colors,
        "team_colors": TEAM_COLORS,
    })