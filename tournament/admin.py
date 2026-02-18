import csv
from django.contrib import admin, messages
from django.http import HttpResponse

from .models import Team, Player, Match, Bracket, Registration, Volunteerapplication

# =========================
# ADMIN ACTIONS
# =========================

@admin.action(description="Export players (CSV)")
def export_players_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="players.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "First Name", "Last Name", "Team",
        "Slot", "Color", "Substitute"
    ])

    for p in queryset.select_related("team"):
        writer.writerow([
            p.first_name,
            p.last_name,
            p.team.team_name if p.team else "",
            p.team.slot_number if p.team else "",
            p.team.team_color if p.team else "",
            p.is_substitute,
        ])

    return response

@admin.action(description="⚠ Reset tournament (DELETE all teams & players)")
def reset_tournament(modeladmin, request, queryset):
    Player.objects.all().delete()
    Team.objects.all().delete()
    messages.success(request, "Tournament reset successfully.")


# =========================
# ADMIN REGISTRATION
# =========================

@admin.action(description="Release slot (make available again)")
def release_slot(modeladmin, request, queryset):
    updated = queryset.update(
        slot_number=None,
        payment_status="pending"
    )
    messages.success(request, f"{updated} slot(s) released.")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("team_name", "slot_number", "team_color", "payment_status")
    list_filter = ("team_color", "payment_status")
    search_fields = ("team_name", "captain_name", "captain_email")
    actions = [release_slot]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "team",
        "games",
        "points",
        "aces",
        "blocks",
        "fouls",
        "is_substitute",
    )

    list_editable = (
        "games",
        "points",
        "aces",
        "blocks",
        "fouls",
    )

    list_filter = ("team", "is_substitute")
    search_fields = ("first_name", "last_name", "team__team_name")
    actions = [export_players_csv]


admin.site.register(Match)
admin.site.register(Bracket)
admin.site.register(Registration)

@admin.register(Volunteerapplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "volunteer_firstname",
        "volunteer_lastname",
        "volunteer_email",
        "volunteer_role",
        "submitted_at",
    )

    search_fields = (
        "volunteer_firstname",
        "volunteer_lastname",
        "volunteer_email",
    )

    list_filter = ("volunteer_role",)

@admin.action(description="Delete selected volunteer applications")
def delete_selected_applications(modeladmin, request, queryset):
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(
        request,
        f"{count} volunteer application(s) were successfully deleted."
    )