from django.dispatch import Signal
from django.dispatch import receiver

from django.conf import settings

user_rest_created = Signal(providing_args=["user"])
user_rest_emailchange = Signal(providing_args=["user"])
user_password_reset = Signal(providing_args=["user"])
user_password_confirm = Signal(providing_args=["user"])

user_existing_invite = Signal(providing_args=["Invite"])
user_email_invite = Signal(providing_args=["Invite"])


@receiver(user_rest_created, dispatch_uid="resturo.signals.send_welcome_mail")
def send_welcome_mail(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_WELCOME", False):
        print("User created")


@receiver(user_rest_emailchange,
          dispatch_uid="resturo.signals.send_email_verification")
def send_email_verification(sender, user, **kwargs):
    if getattr(settings, "RESTURO_VERIFY_EMAIL", False):
        print("Email changed")


@receiver(user_password_reset,
          dispatch_uid="resturo.signals.send_password_mail")
def send_password_mail(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_PASSWORDRESET", False):
        print("User password reset")


@receiver(user_password_confirm,
          dispatch_uid="resturo.signals.send_password_confirm_mail")
def send_password_confirm_mail(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_PASSWORDRESET", False):
        print("User password confirm")


@receiver(user_existing_invite,
          dispatch_uid="resturo.signals.send_invite_user")
def send_invite_user(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_INVITE", False):
        print("User invite")


@receiver(user_email_invite, dispatch_uid="resturo.signals.send_invite_email")
def send_invite_email(sender, user, **kwargs):
    if getattr(settings, "RESTURO_SEND_INVITE", False):
        print("Email invite")
