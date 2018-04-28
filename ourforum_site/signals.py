from django.db.models.signals import post_save
# from django.conf import settings
from ourforum_site.settings import base as settings
# from django.contrib.auth.models import User

from ourforum.models import create_user_profile

User = settings.AUTH_USER_MODEL

post_save.connect(create_user_profile, sender=User)