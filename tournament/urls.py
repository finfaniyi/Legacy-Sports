from django.urls import path
from .views import team_list
from . import views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticViewSitemap  # This is the correct import
from django.conf import settings
from django.conf.urls.static import static

sitemaps = {
    'static': StaticViewSitemap,
}
urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("history/", views.history, name="history"),
    path("media/", views.media, name="media"),
    path("waiver/", views.waiver, name="waiver"),
    path("teams/", views.team_list, name="teams"),
    path("support/", views.support, name="support"),
    path("join_team/", views.join_team, name="join_team"),
    path("instagram-image/", views.instagram_image_proxy, name="instagram_image"),
    path("contact/", views.contact_us, name="contact_us"),
    path("registration/", views.registration, name="registration"),
    path("registration/team/", views.registration_team, name="registration_team"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
    path("registration-success/", views.registration_success, name="registration_success"),
    path("team-brackets/", views.team_brackets, name="team_brackets"),
    path("free-agent/", views.free_agent_signup, name="free_agent_signup"),
    path("free-agent-pool/", views.free_agent_pool, name="free_agent_pool"),
    path("edit-free-agent/<uuid:token>/", views.edit_free_agent, name="edit_free_agent"),
    path("tourney-info/", views.tourney_info, name="tourney_info"),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('page/<slug>/', views.page_detail, name='page_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)