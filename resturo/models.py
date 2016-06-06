import uuid

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.conf import settings
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured


class ModelResolver(object):

    def __call__(self, name):
        model_path = getattr(self, name)

        try:
            app_label, model_class_name = model_path.split('.')
        except ValueError:
            raise ImproperlyConfigured(
                "{0} must be of the form 'app_label.model_name'".format(name))

        model = apps.get_model(app_label, model_class_name)
        if model is None:
            raise ImproperlyConfigured(
                "{0} refers to model '{1}' that has not been "
                "installed".format(name, model_path))

        return model

    def __getattr__(self, name):
        # resolveclass
        if name == 'User':
            model = settings.AUTH_USER_MODEL
        else:
            try:
                model_path = settings.MODELS[name]
            except (KeyError, AttributeError):
                raise ImproperlyConfigured(
                    "no MODELS have been configured, {0} can't be resolved"
                    .format(name))

            model = model_path

        return model


modelresolver = ModelResolver()


class Organization(models.Model):

    class Meta:
        abstract = True

    name = models.TextField()
    members = models.ManyToManyField(modelresolver.User,
                                     through=modelresolver.Membership,
                                     related_name="organizations")

    def __unicode__(self):
        return self.name

    __str__ = __unicode__


class Membership(models.Model):

    class Meta:
        abstract = True

    user = models.ForeignKey(modelresolver.User)
    organization = models.ForeignKey(modelresolver.Organization)
    role = models.IntegerField(default=0)


class EmailVerification(models.Model):
    user = models.OneToOneField(modelresolver.User,
                                related_name="verification")
    previous = models.EmailField(default='')
    verified = models.BooleanField(default=False)
    token = models.CharField(max_length=36, default='')

    def reset(self):
        """ reset verification, meaning state becomes unverified
            and a new token is genereated
        """
        self.verified = False
        self.token = str(uuid.uuid4())
        self.save()


class Invite(models.Model):

    class Meta:
        abstract = True

    user = models.ForeignKey(modelresolver.User, related_name="invites",
                             null=True)
    organization = models.ForeignKey(modelresolver.Organization)
    email = models.EmailField(blank=True)
    strict = models.BooleanField(default=False)
    role = models.IntegerField(default=0)
    token = models.CharField(max_length=36, default='')


@receiver(post_save, sender=modelresolver.User,
          dispatch_uid="resturo.models.reset_verification")
def reset_verification(sender, instance, created=False, *args, **kwargs):
    if getattr(settings, "RESTURO_VERIFY_EMAIL", False):
        if created:
            verification = EmailVerification(user=instance)
            verification.reset()
