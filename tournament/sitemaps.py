from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):

    def items(self):
        return [
            "home",
            "about",
            "history",
            "media",
            "teams",
            "support",
            "join_team",
            "contact_us",
            "registration",
            "team_brackets",
            "tourney_info",
            "waiver",
        ]

    def location(self, item):
        return reverse(item)