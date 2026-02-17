from django.db import IntegrityError
from django.shortcuts import render,redirect
from django.utils import timezone
from .models import Team,Player,Volunteerapplication,TEAM_COLORS
from django.core.mail import send_mail
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings


# Create your views here.
def test_email(request):
    send_mail(
        subject="Legacy Sports Test Email",
        message="This is a test email from your Django setup.",
        from_email=None,
        recipient_list=["yourpersonalemail@gmail.com"],
        fail_silently=False,
    )
    return HttpResponse("Email Sent!")

def team_list(request):
    teams = Team.objects.filter(
        payment_status="paid"
    ).order_by("slot_number")

    return render(request, "tournament/teams.html", {
        "teams": teams
    })
    
def join_team(request):

    if request.method == "POST":

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        age = request.POST.get("age")
        role = request.POST.get("role_interest")
        experience = request.POST.get("experience")

        # Basic validation
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


        # Save to database
        volunteer = Volunteerapplication.objects.create(
            volunteer_firstname=first_name,
            volunteer_lastname=last_name,
            volunteer_email=email,
            volunteer_phone=phone,
            volunteer_age=age if age else None,
            volunteer_role=role,
            why_interested=experience
        )

        # ✅ Confirmation to volunteer
        send_mail(
            subject="Legacy Sports Volunteer Application Received 🤝",
            message=f"""
        Hi {first_name},

        Thank you for applying to join Legacy Sports.

        Role Applied For: {role}

        We’ve received your application and will reach out soon if there's a good fit.

        We appreciate you wanting to build something bigger than yourself.

        — Legacy Sports
        info@legacysportscanada.ca
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        # ✅ Notify YOU (admin)
        send_mail(
            subject="🚨 New Volunteer Application - Legacy Sports",
            message=f"""
        New volunteer application received:

        Name: {first_name} {last_name}
        Email: {email}
        Phone: {phone}
        Age: {age}
        Role: {role}

        Experience:
        {experience}

        Check admin panel for full details.
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["legacysportscanada@gmail.com"],
            fail_silently=False,
        )


        messages.success(request, "Your application has been submitted successfully! We’ll be in touch soon.")
        return redirect("join_team")


    return render(request, "tournament/join_team.html")

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

def team_brackets(request):
    return render(request, "tournament/team_brackets.html")

def tourney_info(request):
    return render(request, "tournament/tourney-info.html")

def contact_us(request):
    return render(request, "tournament/contact_us.html")

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

            captain_name = team.captain_name
            captain_email = team.captain_email
            team_name = team.team_name
            captain_phone = team.captain_phone

            # ✅ Send confirmation to captain
            send_mail(
                subject="Legacy Sports Team Registration Received 🏆",
                message=f"""
        Hi {captain_name},

        Your team "{team_name}" has been successfully registered.

        Slot: {slot}
        Team Color: {team_color}

        Next step:
        Please complete payment using the Stripe link you are being redirected to.

        We’ll confirm your spot once payment is processed.

        — Legacy Sports
        info@legacysportscanada.ca
        """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[captain_email],
                fail_silently=False,
            )

            # ✅ Notify YOU (admin)
            send_mail(
                subject="🚨 New Team Registration - Legacy Sports",
                message=f"""
        New team registered:

        Team Name: {team_name}
        Captain: {captain_name}
        Email: {captain_email}
        Phone: {captain_phone}
        Color: {team_color}
        Slot: {slot}
        Payment Status: Pending

        Login to admin panel to manage.
        """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["legacysportscanada@gmail.com"],
                fail_silently=False,
            )

            STRIPE_PAYMENT_LINK = "https://buy.stripe.com/7sYaEX6ejdPjfrL0jb6wE00"
            request.session.pop("waiver_accepted", None)

            return redirect(STRIPE_PAYMENT_LINK)

    # GET → show form
    return render(request, "tournament/registration-form.html", {
        "taken_colors": taken_colors,
        "team_colors": TEAM_COLORS,
    })
