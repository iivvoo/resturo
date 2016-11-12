import factory
import random
from django.contrib.auth import get_user_model

from ..models import modelresolver


class OrganizationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = modelresolver("Organization")

    name = 'Acme INC.'


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = get_user_model()

    username = factory.LazyAttribute(lambda o: '{0}.{1}{2}'.format(
        o.first_name, o.last_name, random.choice(range(1000))).lower())
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


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
    inviter = factory.SubFactory(UserFactory)
    strict = False
    role = 0


def user_with_org(username, orgname):
    """ create a user linked to an organization.
        password is equal to username.
        Returns user and org  """
    user = UserFactory.create(username=username,
                              email=username + '@example.com')
    user.set_password(username)
    user.save()
    organization = OrganizationFactory.create(name=orgname)
    organization.save()
    modelresolver("Membership").objects.get_or_create(user=user,
                                                      organization=organization,
                                                      role=1)
    return user, organization
