from django.urls import path
from .views import team_list
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("history/", views.history, name="history"),
    path("media/", views.media, name="media"),
    path("waiver/", views.waiver, name="waiver"),
    path("teams/", views.team_list, name="teams"),
    path("support/", views.support, name="support"),
    path("join_team/", views.join_team, name="join_team"),
    path("registration/", views.registration, name="registration"),
    path("registration/team/", views.registration_team, name="registration_team"),
    path("registration/success/", views.registration_success, name="registration_success"),
    path("tourney-info/", views.tourney_info, name="tourney_info"),
]