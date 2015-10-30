import factory
from django.contrib.auth import get_user_model


class OrganizationFactory(factory.Factory):

    name = 'Acme INC.'


class UserFactory(factory.Factory):
    class Meta:
        model = get_user_model()

    username = 'jdoe'
    first_name = 'John'
    last_name = 'Doe'
    email = 'john.doe@example.com'
