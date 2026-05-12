import os

from django.core.management.base import BaseCommand

from tournament.models import Creator, MediaItem


class Command(BaseCommand):

    help = "Bulk import media folders"

    def handle(self, *args, **kwargs):

        BASE_DIR = "media_uploads"

        for creator_folder in os.listdir(BASE_DIR):

            folder_path = os.path.join(
                BASE_DIR,
                creator_folder
            )

            if not os.path.isdir(folder_path):
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

            for filename in os.listdir(folder_path):

                file_path = os.path.join(
                    folder_path,
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

                with open(file_path, "rb") as f:

                    media_item = MediaItem(
                        creator=creator,
                        title=title,
                        category="creative",
                        media_type=media_type,
                    )

                    media_item.media_file.save(
                        filename,
                        f,
                        save=True
                    )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Uploaded: {filename}"
                    )
                )