from django.dispatch import Signal
from django.dispatch import receiver

from django.conf import settings

user_rest_created = Signal(providing_args=["user"])


@receiver(user_rest_created, dispatch_uid="resturo.signals.send_welcome_mail")
def send_welcome_mail(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_WELCOME"):
        print("User created")
