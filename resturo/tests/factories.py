import factory
from django.contrib.auth import get_user_model


class OrganizationFactory(factory.django.DjangoModelFactory):

    name = 'Acme INC.'


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = 'jdoe'
    first_name = 'John'
    last_name = 'Doe'
    email = 'john.doe@example.com'
