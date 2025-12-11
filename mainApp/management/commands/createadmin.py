"""
Deprecated: use environment-driven setup in build.sh.
This management command is intentionally disabled.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Deprecated: use environment-driven setup in build.sh.'

    def handle(self, *args, **options):
        raise SystemExit('createadmin is deprecated. Use ADMIN_USERNAME/ADMIN_PASSWORD with build.sh')
