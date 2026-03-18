"""
Management command to convert all existing product images to WebP.

Usage:
    python manage.py convert_images_to_webp
    python manage.py convert_images_to_webp --dry-run
"""
import io
import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from PIL import Image as PILImage

from catalog.models import ProductImage


class Command(BaseCommand):
    help = "Convert all existing product images to WebP format"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List images that would be converted without actually converting them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        images = ProductImage.objects.exclude(image='')
        total = images.count()
        converted = 0
        skipped = 0
        errors = 0

        self.stdout.write(f"Found {total} product image(s).")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no files will be changed.\n"))

        for pi in images:
            name = pi.image.name
            if not name or name.lower().endswith('.webp'):
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f"  Would convert: {name}")
                converted += 1
                continue

            try:
                with default_storage.open(name, 'rb') as f:
                    img = PILImage.open(f)
                    img.load()

                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')

                buffer = io.BytesIO()
                img.save(buffer, format='WEBP', quality=82, method=6)
                buffer.seek(0)

                webp_name = os.path.splitext(name)[0] + '.webp'
                default_storage.save(webp_name, ContentFile(buffer.read()))
                default_storage.delete(name)

                ProductImage.objects.filter(pk=pi.pk).update(image=webp_name)
                self.stdout.write(f"  Converted: {name} -> {webp_name}")
                converted += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error converting {name}: {e}"))
                errors += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done. Converted: {converted} | Skipped (already WebP): {skipped} | Errors: {errors}"
        ))
