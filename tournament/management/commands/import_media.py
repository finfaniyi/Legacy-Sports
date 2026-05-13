import os

import cloudinary.uploader

from django.core.management.base import BaseCommand

from tournament.models import Creator, MediaItem


CATEGORY_MAP = {
    "2024_LS_Basketball": "2024",
    "2026_LS_Volleyball": "2026",
    "2026_LS_BTS": "bts",
    "2026_LS_Creatives": "creative",
}

class Command(BaseCommand):

    help = "Bulk import media folders"

    def handle(self, *args, **kwargs):

        BASE_DIR = "media_uploads"

        for category_folder in os.listdir(BASE_DIR):

            category_path = os.path.join(
                BASE_DIR,
                category_folder
            )

            if not os.path.isdir(category_path):
                continue

            category = CATEGORY_MAP.get(
                category_folder,
                "Creative Showcase"
            )

            for creator_folder in os.listdir(category_path):

                creator_path = os.path.join(
                    category_path,
                    creator_folder
                )

                if not os.path.isdir(creator_path):
                    continue

                creator_name = creator_folder.replace("_", " ")

                creator = Creator.objects.filter(
                    name__iexact=creator_name
                ).first()

                if not creator:

                    self.stdout.write(
                        self.style.WARNING(
                            f"Creator not found: {creator_name}"
                        )
                    )

                    continue

                for filename in os.listdir(creator_path):

                    file_path = os.path.join(
                        creator_path,
                        filename
                    )

                    if not os.path.isfile(file_path):
                        continue

                    lower = filename.lower()

                    media_type = "image"

                    if lower.endswith((
                        ".mp4",
                        ".mov",
                        ".avi",
                        ".webm"
                    )):
                        media_type = "video"

                    title = os.path.splitext(filename)[0]

                    upload_result = cloudinary.uploader.upload(
                        file_path,
                        resource_type="auto"
                    )
                    
                    existing = MediaItem.objects.filter(
                        title=title,
                        creator=creator,
                        category=category
                    ).exists()

                    if existing:

                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipped duplicate: {filename}"
                            )
                        )

                        continue

                    MediaItem.objects.create(
                        creator=creator,
                        title=title,
                        category=category,
                        media_type=media_type,
                        media_file=upload_result["secure_url"]
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Uploaded: {filename}"
                        )
                    )