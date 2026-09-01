from django.urls import path
from . import views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap
from django.conf import settings
from django.conf.urls.static import static


sitemaps = {
    "static": StaticViewSitemap,
}


urlpatterns = [
    # MAIN SITE
    path("", views.home, name="home"),
    path("events/", views.events, name="events"),
    path("about/", views.about, name="about"),
    path("media/", views.media, name="media"),
    path("support/", views.support, name="support"),
    path("involvement/", views.involvement, name="involvement"),
    path("meet-the-team/", views.meet_the_team, name="meet_the_team"),
    path("contact/", views.contact_us, name="contact_us"),
    path("instagram-image/", views.instagram_image_proxy, name="instagram_image"),

    # HISTORY
    path("history/", views.history, name="history"),
    path("history/2024-basketball/", views.history_2024_basketball, name="history_2024_basketball"),
    path("history/2026-volleyball/", views.history_2026_volleyball, name="history_2026_volleyball"),

    # 2027 BASKETBALL
    path("events/2027/basketball/", views.basketball_2027_info, name="basketball_2027_info"),
    path("events/2027/basketball/teams/", views.basketball_2027_teams, name="basketball_2027_teams"),
    path("events/2027/basketball/bracket/", views.basketball_2027_bracket, name="basketball_2027_bracket"),
    path("events/2027/basketball/standings/", views.basketball_2027_standings, name="basketball_2027_standings"),
    path("events/2027/basketball/live-scores/", views.basketball_2027_live_scores, name="basketball_2027_live_scores"),

    # 2027 SOCCER
    path("events/2027/soccer/", views.soccer_2027_info, name="soccer_2027_info"),
    path("events/2027/soccer/teams/", views.soccer_2027_teams, name="soccer_2027_teams"),
    path("events/2027/soccer/bracket/", views.soccer_2027_bracket, name="soccer_2027_bracket"),
    path("events/2027/soccer/standings/", views.soccer_2027_standings, name="soccer_2027_standings"),
    path("events/2027/soccer/live-scores/", views.soccer_2027_live_scores, name="soccer_2027_live_scores"),

    # 2027 VOLLEYBALL
    path("events/2027/volleyball/", views.volleyball_2027_info, name="volleyball_2027_info"),
    path("events/2027/volleyball/teams/", views.volleyball_2027_teams, name="volleyball_2027_teams"),
    path("events/2027/volleyball/bracket/", views.volleyball_2027_bracket, name="volleyball_2027_bracket"),
    path("events/2027/volleyball/standings/", views.volleyball_2027_standings, name="volleyball_2027_standings"),
    path("events/2027/volleyball/live-scores/", views.volleyball_2027_live_scores, name="volleyball_2027_live_scores"),

    # EXISTING REGISTRATION
    path("registration/", views.registration, name="registration"),
    path("registration/team/", views.registration_team, name="registration_team"),
    path("registration-success/", views.registration_success, name="registration_success"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),

    # EXISTING TOURNAMENT PAGES
    path("waiver/", views.waiver, name="waiver"),
    path("teams/", views.team_list, name="teams"),
    path("team-brackets/", views.team_brackets, name="team_brackets"),
    path("tourney-info/", views.tourney_info, name="tourney_info"),
    path("standings/", views.standings, name="standings"),
    path("live-scores/", views.live_scores, name="live_scores"),

    # FREE AGENT
    path("free-agent/", views.free_agent_signup, name="free_agent_signup"),
    path("free-agent-pool/", views.free_agent_pool, name="free_agent_pool"),
    path("edit-free-agent/<uuid:token>/", views.edit_free_agent, name="edit_free_agent"),

    # OTHER
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("page/<slug>/", views.page_detail, name="page_detail"),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
