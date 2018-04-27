from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from lbforum.models import OurForumUserProfile


class Command(BaseCommand):
    help = "Init OurForumUserProfile"

    def handle(self, **options):
        users = User.objects.all()
        for o in users:
            try:
                o.lbforum_profile
            except OurForumUserProfile.DoesNotExist:
                OurForumUserProfile.objects.create(user=o)
