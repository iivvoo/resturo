import factory
from django.contrib.auth import get_user_model

from ..models import modelresolver


class OrganizationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = modelresolver("Organization")

    name = 'Acme INC.'


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = get_user_model()

    username = 'jdoe'
    first_name = 'John'
    last_name = 'Doe'
    email = 'john.doe@example.com'


class MembershipFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = modelresolver("Membership")

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)


class InviteFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = modelresolver("Invite")

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    strict = False
    role = 0
