from django.db import IntegrityError
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import (
    Team, Player, Volunteerapplication, TEAM_COLORS, FreeAgent, Creator, MediaItem, Match,
    BasketballTeam, BasketballPlayer, BasketballMatch,
    SoccerTeam, SoccerPlayer, SoccerMatch,
    VolleyballTeam, VolleyballPlayer, VolleyballMatch,
)
from django.core.mail import send_mail
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import stripe
from .models import Page
from .models import MediaItem
from django.views.decorators.csrf import csrf_exempt
import requests
import feedparser
import random
import re
from django.db.models import Q
from zoneinfo import ZoneInfo
from django.urls import reverse



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

def events(request):
    return render(request, "tournament/events/events.html")

def support(request):
    return render(request, "tournament/about/support.html")

def about(request):
    return render(request, "tournament/about/about.html")

def history(request):
    return render(request, "tournament/history/history.html")

def history_2024_basketball(request):
    return render(
        request,
        "tournament/history/history_2024_basketball.html"
    )

def history_2026_volleyball(request):
    return render(
        request,
        "tournament/history/history_2026_volleyball.html"
    )

def standings(request):

    standings_data = []

    teams = Team.objects.filter(payment_status="paid")

    for team in teams:

        wins = Match.objects.filter(
            winner=team,
            is_finished=True
        ).count()

        losses = Match.objects.filter(
            is_finished=True
        ).filter(
            team_1=team
        ).exclude(winner=team).count() + Match.objects.filter(
            is_finished=True
        ).filter(
            team_2=team
        ).exclude(winner=team).count()

        pf = 0
        pa = 0

        matches = Match.objects.filter(
            Q(team_1=team) | Q(team_2=team),
            is_finished=True
        )

        for match in matches:

            if match.team_1 == team:
                pf += match.team_1_score
                pa += match.team_2_score
            else:
                pf += match.team_2_score
                pa += match.team_1_score

        standings_data.append({
            "team": team,
            "wins": wins,
            "losses": losses,
            "pf": pf,
            "pa": pa,
            "diff": pf - pa,
        })

    standings_data.sort(
        key=lambda x: (x["wins"], x["diff"]),
        reverse=True
    )

    return render(
        request,
        "tournament/standings.html",
        {"standings": standings_data}
    )
    
def live_scores(request):

    live_matches = Match.objects.filter(
        is_live=True
    )

    completed_matches = Match.objects.filter(
        is_finished=True
    ).order_by("-match_time")[:10]

    return render(
        request,
        "tournament/live_scores.html",
        {
            "live_matches": live_matches,
            "completed_matches": completed_matches,
        }
    )    
    
def media(request):

    media_items = MediaItem.objects.select_related(
        "creator"
    ).order_by("-uploaded_at")

    creators = Creator.objects.all().order_by("name")

    return render(request, "tournament/media/media.html", {
        "media_items": media_items,
        "creators": creators,
    })

def tourney_info(request):
    return render(request, "tournament/events/2026/tourney-info.html")

def contact_us(request):
    return render(request, "tournament/about/contact_us.html")

def team_brackets(request):
    return render(request, "tournament/team_brackets.html")

# =========================
# 2027 EVENT SYSTEMS
# =========================

TOURNAMENT_2027 = {
    "basketball": {"team": BasketballTeam, "player": BasketballPlayer, "match": BasketballMatch, "name": "Basketball", "max_teams": 8, "min_players": 6, "max_players": 8, "price": 2000},
    "soccer": {"team": SoccerTeam, "player": SoccerPlayer, "match": SoccerMatch, "name": "Soccer", "max_teams": 8, "min_players": 7, "max_players": 8, "price": 2000},
    "volleyball": {"team": VolleyballTeam, "player": VolleyballPlayer, "match": VolleyballMatch, "name": "Volleyball", "max_teams": 8, "min_players": 6, "max_players": 8, "price": 2000},
}

def _event_template(sport, page):
    return f"tournament/events/2027/{sport}/{sport}_{page}.html"

def _event_teams(request, sport):
    teams = TOURNAMENT_2027[sport]["team"].objects.filter(payment_status="paid").order_by("slot_number")
    return render(request, _event_template(sport, "teams"), {"teams": teams})

def _event_standings(request, sport):
    cfg = TOURNAMENT_2027[sport]
    data = []
    for team in cfg["team"].objects.filter(payment_status="paid"):
        matches = cfg["match"].objects.filter(Q(team_1=team) | Q(team_2=team), is_finished=True)
        wins = matches.filter(winner=team).count()
        pf = pa = 0
        for match in matches:
            if match.team_1_id == team.id:
                pf += match.team_1_score; pa += match.team_2_score
            else:
                pf += match.team_2_score; pa += match.team_1_score
        data.append({"team": team, "games_played": matches.count(), "wins": wins, "losses": matches.exclude(winner=team).count(), "pf": pf, "pa": pa, "diff": pf-pa, "points": wins*3})
    data.sort(key=lambda x: (x["wins"], x["diff"]), reverse=True)
    return render(request, _event_template(sport, "standings"), {"standings": data})

def _event_live_scores(request, sport):
    matches = TOURNAMENT_2027[sport]["match"].objects.select_related("team_1", "team_2", "winner").order_by("-is_live", "-match_time")
    return render(request, _event_template(sport, "live_scores"), {"matches": matches})

def _event_bracket(request, sport):
    M = TOURNAMENT_2027[sport]["match"]
    q = M.objects.filter(round_name="quarter").select_related("team_1", "team_2", "winner").order_by("match_time")
    s = M.objects.filter(round_name="semi").select_related("team_1", "team_2", "winner").order_by("match_time")
    f = M.objects.filter(round_name="final").select_related("team_1", "team_2", "winner").order_by("match_time")
    final = f.filter(is_finished=True).first()
    return render(request, _event_template(sport, "team_brackets"), {"bracket_ready": q.exists() or s.exists() or f.exists(), "quarterfinals": q, "semifinals": s, "finals": f, "champion": final.winner if final else None})

def _event_registration(request, sport):
    cfg = TOURNAMENT_2027[sport]; T = cfg["team"]
    T.objects.filter(payment_status="pending", waiver_timestamp__lt=timezone.now()-timedelta(minutes=10)).delete()
    teams = T.objects.filter(payment_status="paid")
    slots = set(teams.values_list("slot_number", flat=True))
    toronto = ZoneInfo("America/Toronto"); now = timezone.now().astimezone(toronto)
    # Keep registration closed until the real dates are set.
    registration_open = datetime(2099,1,1,0,0,0,tzinfo=toronto)
    registration_close = datetime(2099,12,31,23,59,59,tzinfo=toronto)
    return render(request, _event_template(sport, "registration_display"), {"taken_slots": slots, "slot_colors": {t.slot_number:t.team_color for t in teams}, "slot_names": {t.slot_number:t.team_name for t in teams}, "now":now, "registration_open":registration_open, "registration_close":registration_close, "full":len(slots)>=cfg["max_teams"], "spots_left":max(0,cfg["max_teams"]-len(slots))})

def _event_registration_team(request, sport):
    cfg=TOURNAMENT_2027[sport]; T=cfg["team"]; P=cfg["player"]
    T.objects.filter(payment_status="pending", waiver_timestamp__lt=timezone.now()-timedelta(minutes=10)).delete()
    paid=T.objects.filter(payment_status="paid")
    used=set(paid.values_list("slot_number",flat=True)); slot=next((i for i in range(1,cfg["max_teams"]+1) if i not in used),None)
    if slot is None: return redirect(f"{sport}_2027_registration")
    taken=set(paid.values_list("team_color",flat=True)); colors=[c for c in TEAM_COLORS if c[0] not in taken]; random.shuffle(colors)
    ctx={"taken_colors":taken,"team_colors":colors,"slot":slot}
    if request.method != "POST": return render(request,_event_template(sport,"registration-form"),ctx)
    color=request.POST.get("team_color"); email=request.POST.get("captain_email")
    if T.objects.filter(team_color=color).exists():
        return render(request,_event_template(sport,"registration-form"),{**ctx,"error":"Color already taken.","form_data":request.POST})
    existing=T.objects.filter(captain_email=email).first()
    if existing:
        if existing.payment_status=="pending": existing.delete()
        else: return render(request,_event_template(sport,"registration-form"),{**ctx,"error":"This email has already registered a team for this tournament.","form_data":request.POST})
    try: count=int(request.POST.get("roster_size",cfg["min_players"]))
    except (TypeError,ValueError): count=cfg["min_players"]
    count=max(cfg["min_players"],min(cfg["max_players"],count))
    team=T.objects.create(slot_number=slot,team_name=request.POST["team_name"],captain_name=request.POST["captain_name"],captain_email=email,captain_phone=request.POST["captain_phone"],team_color=color,player_count=count,payment_status="pending",waiver_agreed=True,spectator_range=request.POST.get("spectator_range") or "",waiver_timestamp=timezone.now())
    try:
        for i in range(1,min(6,count)+1):
            age=request.POST.get(f"player_{i}_age")
            if not age: raise ValueError(f"Player {i} age is required.")
            P.objects.create(team=team,first_name=request.POST.get(f"player_{i}_first"),last_name=request.POST.get(f"player_{i}_last"),age=int(age),gender=request.POST.get(f"player_{i}_gender"),contact_email=request.POST.get(f"player_{i}_email"),contact_phone=request.POST.get(f"player_{i}_phone"),school=request.POST.get(f"player_{i}_school") or "",is_substitute=False)
        for n in range(7,count+1):
            k=n-6; age=request.POST.get(f"sub_{k}_age")
            if not age: raise ValueError(f"Player {n} age is required.")
            P.objects.create(team=team,first_name=request.POST.get(f"sub_{k}_first"),last_name=request.POST.get(f"sub_{k}_last"),age=int(age),gender=request.POST.get(f"sub_{k}_gender"),contact_email=request.POST.get(f"sub_{k}_email"),contact_phone=request.POST.get(f"sub_{k}_phone"),school=request.POST.get(f"sub_{k}_school") or "",is_substitute=True)
    except (TypeError,ValueError) as exc:
        team.delete(); return render(request,_event_template(sport,"registration-form"),{**ctx,"error":str(exc),"form_data":request.POST})
    checkout=stripe.checkout.Session.create(payment_method_types=["card"],line_items=[{"price_data":{"currency":"cad","product_data":{"name":f"Legacy Sports 2027 {cfg['name']} Team Entry ({count} players)"},"unit_amount":count*cfg["price"]},"quantity":1}],mode="payment",success_url=request.build_absolute_uri(reverse(f"{sport}_2027_registration_success")+"?session_id={CHECKOUT_SESSION_ID}"),cancel_url=request.build_absolute_uri(reverse(f"{sport}_2027_registration_team")),metadata={"sport":sport,"year":"2027","team_id":str(team.id),"slot":str(slot)})
    return redirect(checkout.url)

def _event_registration_success(request,sport):
    if not request.GET.get("session_id"): return redirect(f"{sport}_2027_registration")
    return render(request,_event_template(sport,"registration_success"))

# Basketball 2027
def basketball_2027_info(request): return render(request,_event_template("basketball","tourney-info"))
def basketball_2027_teams(request): return _event_teams(request,"basketball")
def basketball_2027_bracket(request): return _event_bracket(request,"basketball")
def basketball_2027_standings(request): return _event_standings(request,"basketball")
def basketball_2027_live_scores(request): return _event_live_scores(request,"basketball")
def basketball_2027_registration(request): return _event_registration(request,"basketball")
def basketball_2027_registration_team(request): return _event_registration_team(request,"basketball")
def basketball_2027_registration_success(request): return _event_registration_success(request,"basketball")

# Soccer 2027
def soccer_2027_info(request): return render(request,_event_template("soccer","tourney-info"))
def soccer_2027_teams(request): return _event_teams(request,"soccer")
def soccer_2027_bracket(request): return _event_bracket(request,"soccer")
def soccer_2027_standings(request): return _event_standings(request,"soccer")
def soccer_2027_live_scores(request): return _event_live_scores(request,"soccer")
def soccer_2027_registration(request): return _event_registration(request,"soccer")
def soccer_2027_registration_team(request): return _event_registration_team(request,"soccer")
def soccer_2027_registration_success(request): return _event_registration_success(request,"soccer")

# Volleyball 2027
def volleyball_2027_info(request): return render(request,_event_template("volleyball","tourney-info"))
def volleyball_2027_teams(request): return _event_teams(request,"volleyball")
def volleyball_2027_bracket(request): return _event_bracket(request,"volleyball")
def volleyball_2027_standings(request): return _event_standings(request,"volleyball")
def volleyball_2027_live_scores(request): return _event_live_scores(request,"volleyball")
def volleyball_2027_registration(request): return _event_registration(request,"volleyball")
def volleyball_2027_registration_team(request): return _event_registration_team(request,"volleyball")
def volleyball_2027_registration_success(request): return _event_registration_success(request,"volleyball")

# =========================
# VOLUNTEER
# =========================

def involvement(request):

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
            return render(request, "tournament/involved/involvement.html", {
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
            message="Plain text fallback",
            html_message=f"""
            <p style="text-align:center; margin-bottom:20px;">
                <img src="https://i.imgur.com/eiG0G9I.png"
                    alt="Legacy Sports Logo"
                    width="220"
                    style="width:220px; max-width:100%; height:auto; display:block; margin:auto;">
            </p>

            <p>Hi {first_name},</p>

            <p>
            Thank you for applying to join the Legacy Sports team - we’re excited to learn more about you</strong>!
            </p>

            <p>
            You applied for: <strong>{role}</strong>
            </p>
            
            <p>
            As part of our selection process, all applicants are invited to complete a mandatory brief interview. You can schedule your interview using the booking link below:
            https://calendar.app.google/Q389hRux7ZpYAhUy9 
            </p>

            <p>
            Please select a time that works best for you. If none of the available times fit your schedule, feel free to reach out to us at legacysportscanada@gmail.com, and we’ll be happy to coordinate an alternative.
            </p>

            <p><strong>Important Dates:</strong></p>
            <ul>
                <li>Application deadline: Monday, May 11th</li>
                <li>Final day for interviews: Friday, May 15th</li>
                <li>Decisions will be shared by Monday, May 18th</li>
            </ul>

            <p>
            Successful applicants will then be invited to a short welcome call, where we’ll introduce the team and share next steps. A follow-up meeting will be scheduled to go over specific roles, responsibilities, and tournament details.
            </p>
            
            <p>
            We truly appreciate your interest in being part of Legacy Sports and helping us build something meaningful in the community.
            </p>
            
            <p>If you have any questions, don’t hesitate to reach out!</p>
            
            <p>
            <strong>Best,</strong>
            </p>
            <p>Legacy Sports Team</p>
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
            Experience / Why they joined:
            {experience}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["legacysportscanada@gmail.com"],
            fail_silently=False,
        )

        messages.success(request, "Application submitted successfully!")
        return redirect("involvement")

    return render(request, "tournament/involved/involvement.html")

# =========================
# REGISTRATION DISPLAY
# =========================

def registration(request):
    Team.objects.filter(
        payment_status="pending"
    ).delete()
    teams = Team.objects.filter(payment_status="paid")

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
        2026, 5, 1, 00, 00, 0,
        tzinfo=toronto
    )

    registration_close = datetime(
        2026, 6, 3, 00, 00, 0,
        tzinfo=toronto
    )

    full = len(taken_slots) >= 8
    spots_left = 8 - len(taken_slots)

    return render(request, "tournament/registration_display.html", {
        "taken_slots": taken_slots,
        "slot_colors": slot_colors,
        "slot_names": slot_names,
        "now": now,
        "registration_open": registration_open,
        "registration_close": registration_close,
        "full": full,
        "spots_left": spots_left,
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

    spectator_range = request.POST.get("spectator_range")

    taken_slots = set(
        Team.objects.filter(payment_status="paid")
        .values_list("slot_number", flat=True)
    )

    slot = None

    for i in range(1, 9):
        if i not in taken_slots:
            slot = i
            break

    if slot is None:
        return redirect("/registration/?error=full")

    taken_colors = set(
        Team.objects.filter(payment_status="paid")
        .values_list("team_color", flat=True)
    )

    if request.method == "POST":
        
        # ✅ CLEAN OLD PENDING TEAMS HERE
        Team.objects.filter(
            payment_status="pending",
            waiver_timestamp__lt=timezone.now() - timedelta(minutes=10)
        ).delete()

        team_color = request.POST.get("team_color")

        existing_team = Team.objects.filter(slot_number=slot).first()

        if existing_team:
            if existing_team.payment_status == "pending":
                if (
                    existing_team.captain_email == request.POST.get("captain_email")
                    or timezone.now() - existing_team.waiver_timestamp > timezone.timedelta(minutes=10)
                ):
                    existing_team.delete()
                else:
                    return redirect("/registration/?error=slot_taken")
            else:
                return redirect("/registration/?error=slot_taken")

        if Team.objects.filter(team_color=team_color).exists():
            return render(request, "tournament/registration-form.html", {
                "error": "Color already taken.",
                "taken_colors": taken_colors,
                "team_colors": available_colors,
            })

        player_count = int(request.POST.get("roster_size", 6))
        player_count = max(6, min(8, player_count))

        captain_email = request.POST.get("captain_email")

        existing_team = Team.objects.filter(captain_email=captain_email).first()

        if existing_team:
            if existing_team.payment_status == "pending":
                # 🔥 allow retry by deleting old pending team
                existing_team.delete()
            else:
                return render(request, "tournament/registration-form.html", {
                    "error": "This email has already registered a team.",
                    "taken_colors": taken_colors,
                    "team_colors": available_colors,
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
                    "team_colors": available_colors,
                })

            try:
                age_value = int(age_value)
            except ValueError:
                return render(request, "tournament/registration-form.html", {
                    "error": f"Player {i} age must be a number.",
                    "taken_colors": taken_colors,
                    "team_colors": available_colors,
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
                    "team_colors": available_colors,
                })

            try:
                sub1_age = int(sub1_age)
            except ValueError:
                return render(request, "tournament/registration-form.html", {
                    "error": "Substitute 1 age must be a number.",
                    "taken_colors": taken_colors,
                    "team_colors": available_colors,
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
                    "team_colors": available_colors,
                })

            try:
                sub2_age = int(sub2_age)
            except ValueError:
                return render(request, "tournament/registration-form.html", {
                    "error": "Substitute 2 age must be a number.",
                    "taken_colors": taken_colors,
                    "team_colors": available_colors,
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
        price_per_player = 2000
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
            cancel_url=request.build_absolute_uri(f"/registration/team/?slot={slot}"),
            metadata={
                "team_id": team.id,
                "slot": slot
            }
        )

        return redirect(checkout_session.url)

    available_colors = [
        color for color in TEAM_COLORS
        if color[0] not in taken_colors
    ]

    random.shuffle(available_colors)
    
    return render(request, "tournament/registration-form.html", {
        "taken_colors": taken_colors,
        "team_colors": available_colors,
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

        # 2027 sport-specific registrations use the same Stripe webhook.
        sport = metadata.get("sport")
        if sport in TOURNAMENT_2027:
            cfg = TOURNAMENT_2027[sport]
            TeamModel = cfg["team"]
            try:
                team = TeamModel.objects.get(id=team_id)
            except TeamModel.DoesNotExist:
                return JsonResponse({"error": "Team not found"}, status=400)
            team.payment_status = "paid"
            team.save(update_fields=["payment_status"])
            send_mail(subject=f"{cfg['name']} 2027 registration: {team.team_name}", message=f"{team.team_name} completed payment for the 2027 {cfg['name']} tournament.", from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=["legacysportscanada@gmail.com"], fail_silently=False)
            return JsonResponse({"status": "success"})

        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            print(f"❌ Team not found: {team_id}")
            return JsonResponse({"error": "Team not found"}, status=400)

        # ✅ Only runs if valid
        team.payment_status = "paid"
        team.save()

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
                    <p style="text-align:center; margin-bottom:20px;">
                        <img src="https://i.imgur.com/eiG0G9I.png"
                            alt="Legacy Sports Logo"
                            width="220"
                            style="width:250px; max-width:100%; height:auto; display:block; margin:auto;">
                    </p>
                    <p>Hello,</p>

                    <p>
                    Your team "<strong>{team.team_name}</strong>" is officially registered for the Legacy Sports volleyball tournament!
                    </p>

                    <p>
                    We are excited to have you join us for a fun day of volleyball, teamwork, and meeting new people.
                    </p>

                    <p>
                    Before you arrive, please complete the 
                    <a href="https://waiver.smartwaiver.com/w/qigvhu5mhwgf5q9khffpb3/web/" target="_blank">
                    waiver form
                    </a> 
                    to help speed up the check-in process. All participants should be ready to show proof of waiver completion, valid ID, and their ticket or registration confirmation at check-in.
                    </p>

                    <p><strong>Team details:</strong></p>
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
                    - Legacy Sports
                    </p>
                    """,
                    
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[player.contact_email],
                    fail_silently=False,
                    reply_to=["legacysportscanada@gmail.com"],
                )

        # Admin notification
        send_mail(
            subject=f"🏐 {team.team_name} • Slot {team.slot_number}",
            message="New team registered.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["legacysportscanada@gmail.com"],
            fail_silently=False,

            html_message=f"""
            <div style="font-family: Arial, sans-serif; background:#f6f7fb; padding:20px;">
                <div style="max-width:480px; margin:auto; background:white; border-radius:10px; padding:20px;">
                    
                    <h2 style="margin:0 0 10px 0;">🏐 New Team</h2>
                    
                    <p><strong>{team.team_name}</strong></p>
                    <p>Slot: {team.slot_number} • Color: {team.team_color}</p>
                    <p>Players: {team.player_count} • {team.payment_status.upper()}</p>
                    
                    <p style="margin-top:10px;">
                        {team.captain_name}<br>
                        {team.captain_email}<br>
                        {team.captain_phone}
                    </p>

                </div>
            </div>
            """
        )

    return JsonResponse({"status": "success"})

def free_agent_signup(request):
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        name = request.POST.get("name")
        ig = request.POST.get("instagram")
        note = request.POST.get("note")

        if form_type == "solo":
            gender = request.POST.get("gender")

            agent = FreeAgent.objects.create(
                name=name,
                gender=gender,
                player_type="solo",
                instagram=ig,
                note=note,
            )

        else:
            needed_players = request.POST.get("needed_players")
            needed_gender = request.POST.get("needed_gender")

            agent = FreeAgent.objects.create(
                name=name,
                gender="group",
                player_type="group",
                instagram=ig,
                note=f"{note} | Needs {needed_players} {needed_gender}",
            )

        edit_url = reverse("edit_free_agent", args=[agent.edit_token])

        return render(request, "tournament/free_agent_success.html", {
            "edit_link": request.build_absolute_uri(edit_url)
        })

    return render(request, "tournament/free_agent_signup.html")

def free_agent_pool(request):
    agents = FreeAgent.objects.all().order_by("-created_at")

    solos = agents.filter(player_type="solo")
    groups = agents.filter(player_type="group")

    return render(request, "tournament/free_agent_pool.html", {
        "solos": solos,
        "groups": groups,
    })
    
    
def edit_free_agent(request, token):
    agent = get_object_or_404(FreeAgent, edit_token=token)

    if request.method == "POST":
        agent.status = request.POST.get("status")
        agent.note = request.POST.get("note")
        agent.save()
        return redirect("free_agent_pool")

    return render(request, "tournament/edit_free_agent.html", {
        "agent": agent
    })
    
def meet_the_team(request):
    return render(request, "tournament/about/meet_the_team.html")

