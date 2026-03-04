# tournament/sitemaps.py
from django.contrib.sitemaps import Sitemap
from .models import Page
from django.urls import reverse

class PageSitemap(Sitemap):
    def items(self):
        return Page.objects.all()  # Fetch all Page model objects

    def lastmod(self, obj):
        return obj.updated_at  # Assuming `updated_at` exists on your Page model

    def location(self, obj):
        return reverse('page_detail', args=[obj.slug])  # Replace 'page_detail' with the actual view name and arguments