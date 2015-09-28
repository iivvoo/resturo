from django.db import models

from django.conf import settings
from django.db.models import get_model
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured

class ModelResolver(object):
    def __getattr__(self, name):
        # resolveclass
        if name == 'User':
            model = get_user_model()
        else:
            try:
                model_path = settings.MODELS[name]
            except (KeyError, AttributeError):
                raise ImproperlyConfigured(
                    "no MODELS have been configured, {0} can't be resolved").format(name)

            try:
                app_label, model_class_name = model_path.split('.')
            except ValueError:
                raise ImproperlyConfigured(
                    "{0} must be of the form 'app_label.model_name'").format(name)

            model = get_model(app_label, model_class_name)
            if model is None:
                raise ImproperlyConfigured(
                    "{0} refers to model '{1}' that has not been "
                    "installed".format(name, model_path))

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

class Membership(models.Model):
    class Meta:
        abstract = True

    user = models.ForeignKey(modelresolver.User)
    organization = models.ForeignKey(modelresolver.Organization)
    role = models.IntegerField(default=0)


