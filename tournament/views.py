from django.db import IntegrityError
from django.shortcuts import render,redirect
from django.utils import timezone
from .models import Team,Player,Volunteerapplication,TEAM_COLORS
from django.core.mail import send_mail
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY



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
            subject="Legacy Sports Volunteer Application Received ⚡",
            message=f"""
                Hi {first_name},

                Thank you for applying to join Legacy Sports Team.

                Role Applied For: {role}

                We have received your application and will reach out soon.

                Thank you and have a good day.

                — Legacy Sports
                info@legacysportscanada.ca
                """,
            from_email=None,  # important
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
    return redirect("/registration/?paid=true")

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

        team_color = request.POST.get("team_color")

        # HARD SLOT LOCK
        if Team.objects.filter(slot_number=slot).exists():
            return redirect("/registration/?error=slot_taken")

        # HARD COLOR LOCK
        if Team.objects.filter(team_color=team_color).exists():
            return render(request, "tournament/registration-form.html", {
                "error": "This color has already been taken.",
                "taken_colors": taken_colors,
                "team_colors": TEAM_COLORS,
            })

        # Save form data temporarily (ONLY AFTER validation)
        request.session["pending_team"] = {
            "slot": slot,
            "team_name": request.POST["team_name"],
            "captain_name": request.POST["captain_name"],
            "captain_email": request.POST["captain_email"],
            "captain_phone": request.POST["captain_phone"],
            "team_color": team_color,
        }

        # Create Stripe Checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "cad",
                    "product_data": {
                        "name": "Legacy Sports Team Entry",
                    },
                    "unit_amount": 1500,
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
            }
        )

        request.session.pop("waiver_accepted", None)

        return redirect(checkout_session.url)

    return render(request, "tournament/registration-form.html", {
        "taken_colors": taken_colors,
        "team_colors": TEAM_COLORS,
    })
    
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except stripe.error.SignatureVerificationError:
        return JsonResponse({"error": "Invalid signature"}, status=400)
    except Exception:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    # ✅ Payment completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        metadata = session.get("metadata", {})

        slot = metadata.get("slot")
        team_name = metadata.get("team_name")
        captain_name = metadata.get("captain_name")
        captain_email = metadata.get("captain_email")
        captain_phone = metadata.get("captain_phone")
        team_color = metadata.get("team_color")

        # Final slot protection
        if not Team.objects.filter(slot_number=slot).exists():

            team = Team.objects.create(
                slot_number=slot,
                team_name=team_name,
                captain_name=captain_name,
                captain_email=captain_email,
                captain_phone=captain_phone,
                team_color=team_color,
                payment_status="paid",
                waiver_agreed=True,
                waiver_timestamp=timezone.now(),
            )

            # ✅ Confirmation Email (SEND HERE, NOT BEFORE)
            send_mail(
                subject="Legacy Sports Team Registration Confirmed ⚡",
                message=f"""
                Hi {captain_name},

                Your team "{team_name}" is officially registered.

                Slot: {slot}
                Team Color: {team_color}

                We can’t wait to see you at the tournament!

                — Legacy Sports
                
                For any questions, Email - legacysportscanada@gmail.com
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[captain_email],
                fail_silently=False,
            )
            
            # ✅ Notify Admin (YOU)
            send_mail(
                subject="🚨 New Paid Team Registration - Legacy Sports",
                message=f"""
                A new team has successfully paid and registered.

                Team Name: {team_name}
                Captain: {captain_name}
                Email: {captain_email}
                Phone: {captain_phone}
                Slot: {slot}
                Color: {team_color}

                Payment confirmed via Stripe.

                Login to admin panel to manage.
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["legacysportscanada@gmail.com"],
                fail_silently=False,
            )

    return JsonResponse({"status": "success"})
