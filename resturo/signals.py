from django.dispatch import Signal
from django.dispatch import receiver

from django.conf import settings

user_rest_created = Signal(providing_args=["user"])
user_password_reset = Signal(providing_args=["user"])
user_password_confirm = Signal(providing_args=["user"])


@receiver(user_rest_created, dispatch_uid="resturo.signals.send_welcome_mail")
def send_welcome_mail(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_WELCOME"):
        print("User created")


@receiver(user_password_reset,
          dispatch_uid="resturo.signals.send_password_mail")
def send_password_mail(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_PASSWORDRESET"):
        print("User password reset")


@receiver(user_password_confirm,
          dispatch_uid="resturo.signals.send_password_confirm_mail")
def send_password_confirm_mail(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_PASSWORDRESET"):
        print("User password confirm")
