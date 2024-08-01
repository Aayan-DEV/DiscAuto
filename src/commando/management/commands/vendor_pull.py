from typing import Any
from django.core.management.base import BaseCommand
import helpers
from django.conf import settings

STATICFILES_VENDOR_DIR = getattr(settings, "STATICFILES_VENDOR_DIR")

VENDOR_STATICFILES = {
    "saas-theme.min.css": "https://raw.githubusercontent.com/codingforentrepreneurs/SaaS-Foundations/main/src/staticfiles/theme/saas-theme.min.css",
    "flowbite.min.css": "https://cdn.jsdelivr.net/npm/flowbite@2.4.1/dist/flowbite.min.css",
    "flowbite.min.js": "https://cdn.jsdelivr.net/npm/flowbite@2.4.1/dist/flowbite.min.js",
    "flowbite.min.js.map":"https://cdnjs.cloudflare.com/ajax/libs/flowbite/2.4.1/flowbite.min.js.map"
}

class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any):
        self.stdout.write("Downloading vendor static files...")
        completed_urls = []
        for name, url in VENDOR_STATICFILES.items():
            out_path = STATICFILES_VENDOR_DIR / name
            dl_success = helpers.download_to_local(url, out_path)
            print(name,url,out_path)
            if dl_success:
                completed_urls.append(url)
            else:
                self.stdout.write(self.style.ERROR(f"Failed to download {name} from {url}"))

        if set(completed_urls) == set(VENDOR_STATICFILES.values()):
           self.stdout.write(self.style.SUCCESS("Successfully updated all vendor static files."))
        else:
            self.stdout.write(self.style.ERROR("Some files were not updated."))
