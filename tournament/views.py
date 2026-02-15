from django.db import IntegrityError
from django.shortcuts import render,redirect
from django.utils import timezone
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

def support(request):
    return render(request, "tournament/support.html")

def join_team(request):
    return render(request, "tournament/join_team.html")

def about(request):
    return render(request, "tournament/about.html")


def history(request):
    return render(request, "tournament/history.html")


def media(request):
    return render(request, "tournament/media.html")

def waiver(request):
    next_url = request.GET.get("next", "/")

    if request.method == "POST":
        request.session["waiver_accepted"] = True
        request.session["waiver_timestamp"] = str(timezone.now())
        return redirect(next_url)

    return render(request, "tournament/waiver.html", {
        "next": next_url
    })

def registration(request):
    teams = Team.objects.all()
    taken_slots = set()
    slot_colors = {}
    slot_names = {}

    

    for team in teams:
        taken_slots.add(team.slot_number)
        slot_colors[team.slot_number] = team.team_color
        slot_names[team.slot_number] = team.team_name

    is_full = len(taken_slots) >= 8
    
    return render(request, "tournament/registration_display.html", {
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

    taken_colors = set(
        Team.objects.values_list("team_color", flat=True)
    )

    if request.method == "POST":
        
        if not request.POST.get("agree_waiver"):
            return render(request, "tournament/registration-form.html", {
            "error": "You must agree to the waiver before proceeding.",
            "taken_colors": taken_colors,
            "team_colors": TEAM_COLORS,
        })


        # ❌ Removed duplicate waiver check here

        # HARD SLOT LOCK
        if Team.objects.filter(slot_number=slot).exists():
            return redirect("/registration/?error=slot_taken")

        team_color = request.POST.get("team_color")

        # HARD COLOR LOCK
        if Team.objects.filter(team_color=team_color).exists():
            return render(request, "tournament/registration-form.html", {
                "error": "This color has already been taken.",
                "taken_colors": taken_colors,
                "team_colors": TEAM_COLORS,
            })

        team = Team.objects.create(
            slot_number=slot,
            team_name=request.POST["team_name"],
            captain_name=request.POST["captain_name"],
            captain_email=request.POST["captain_email"],
            captain_phone=request.POST["captain_phone"],
            team_color=team_color,
            payment_status="pending",
            waiver_agreed=True,
            waiver_timestamp=timezone.now(),
        )

        # Players logic stays exactly as you have it

        STRIPE_PAYMENT_LINK = "https://buy.stripe.com/7sYaEX6ejdPjfrL0jb6wE00"

        # 🔥 Clear waiver session after successful registration
        request.session.pop("waiver_accepted", None)

        return redirect(STRIPE_PAYMENT_LINK)

    # GET → show form
    return render(request, "tournament/registration-form.html", {
        "taken_colors": taken_colors,
        "team_colors": TEAM_COLORS,
    })
