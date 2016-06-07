import unittest

from django.test import TestCase
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse
from rest_framework import status

from rest_framework.test import APITestCase
from mock_django.signals import mock_signal_receiver

from .factories import OrganizationFactory as OrganizationFactoryBase
from .factories import UserFactory, MembershipFactory, InviteFactory

from .models import Organization, Invite, Membership
from resturo.serializers import JoinSerializer

from resturo.models import EmailVerification

from resturo.signals import user_password_reset, user_rest_created
from resturo.signals import user_existing_invite, user_email_invite


class OrganizationFactory(OrganizationFactoryBase):

    class Meta:
        model = Organization


class TestModels(unittest.TestCase):

    def test_organization(self):
        o = OrganizationFactory.create(name="test")
        o.save()


class TestUserCreation(APITestCase):

    def test_signal_fired_create_success(self):

        with mock_signal_receiver(user_rest_created) as receiver:
            self.client.post(reverse('resturo_user_create'),
                             {'username': 'john.doe',
                              'first_name': 'john',
                              'last_name': 'Doe',
                              'email': 'john.doe@example.com',
                              'password': 'g3h31m'})
            self.assertEqual(receiver.call_count, 1)


class TestPasswordReset(APITestCase):

    def test_signal_fired_initial_success(self):
        UserFactory(email="test@example.com")

        with mock_signal_receiver(user_password_reset) as receiver:
            self.client.get(reverse('resturo_user_reset'),
                            {'handle': 'test@example.com'})
            self.assertEqual(receiver.call_count, 1)


class TestEmailVerify(APITestCase):

    def test_succeed(self):
        u = UserFactory()
        v = EmailVerification(user=u)
        v.reset()

        response = self.client.get(reverse('resturo_user_verify'),
                                   {'token': v.token})
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        v = EmailVerification.objects.get(pk=v.id)
        self.assertTrue(v.verified)

    def test_no_verify(self):
        u = UserFactory()

        response = self.client.get(reverse('resturo_user_verify'),
                                   {'token': "some token"})
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        u = User.objects.get(pk=u.id)
        with self.assertRaises(EmailVerification.DoesNotExist):
            u.verification

    def test_already_verified(self):
        u = UserFactory()
        v = EmailVerification.objects.create(user=u, verified=True)

        response = self.client.get(reverse('resturo_user_verify'),
                                   {'token': v.token})
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        v = EmailVerification.objects.get(pk=v.id)
        self.assertTrue(v.verified)

    def test_fail(self):
        u = UserFactory()
        v = EmailVerification(user=u)
        v.reset()

        response = self.client.get(reverse('resturo_user_verify'),
                                   {'token': 'totally-wrong-token'})
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        v = EmailVerification.objects.get(pk=v.id)
        self.assertFalse(v.verified)


class TestInviteModel(TestCase):

    def test_token_generation(self):
        """ a new invite should get a token """
        o = OrganizationFactory.create()
        u = UserFactory.create()
        i = Invite(organization=o, user=u)
        i.save()

        self.assertTrue(i.token)
        self.assertEquals(len(i.token), 36)

    def test_token_update(self):
        """ Updating an invite should change the token """
        i = InviteFactory.create()
        token = i.token
        i.save()
        self.assertEqual(token, i.token)


class TestCreateInvite(APITestCase):

    # for now: invites only for admin
    # add inviter to invite?
    # embed invites in user serialization (?), or make it separate endpoint?
    def test_working_invite(self):
        o = OrganizationFactory.create()

        response = self.client.post(reverse('resturo_organization_invite',
                                            kwargs={'pk': o.pk}),
                                    {"handle": "test@example.com",
                                     "role": 2,
                                     "strict": False})

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(Invite.objects.count(), 1)
        self.assertEquals(Invite.objects.first().organization, o)

    def test_missing_handle(self):
        o = OrganizationFactory.create()

        response = self.client.post(reverse('resturo_organization_invite',
                                            kwargs={'pk': o.pk}),
                                    {
            "role": 2,
            "strict": False})

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Invite.objects.count(), 0)

    def test_not_user_and_not_email(self):
        """ if the handle doesn't match a user, it must look like an
            email """
        o = OrganizationFactory.create()

        response = self.client.post(reverse('resturo_organization_invite',
                                            kwargs={'pk': o.pk}),
                                    {"handle": "does not exist",
                                     "role": 2,
                                     "strict": False})

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Invite.objects.count(), 0)

    def test_already_member(self):
        m = MembershipFactory.create(user__email="test@example.com")

        response = self.client.post(reverse('resturo_organization_invite',
                                            kwargs={'pk': m.organization.pk}),
                                    {"handle": "test@example.com",
                                     "role": 2,
                                     "strict": False})

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(response.data['non_field_errors'][0],
                          "User is already member")
        self.assertEquals(Invite.objects.count(), 0)

    def test_user_signal_fired(self):
        """ Existing user gets invited should fire user_existing_invite
            signal """
        u = UserFactory.create(username="test", email="test@example.com")
        o = OrganizationFactory.create(name="Second org")

        with mock_signal_receiver(user_existing_invite) as receiver:
            self.client.post(reverse('resturo_organization_invite',
                                     kwargs={'pk': o.pk}),
                             {"handle": u.username,
                              "role": 2,
                              "strict": False})
            self.assertEqual(receiver.call_count, 1)

    def test_email_signal_fired(self):
        """ Non existing user gets invited by email, should fire
            user_email_invite signal """
        o = OrganizationFactory.create(name="Second org")

        with mock_signal_receiver(user_email_invite) as receiver:
            self.client.post(reverse('resturo_organization_invite',
                                     kwargs={'pk': o.pk}),
                             {"handle": "test@example.com",
                              "role": 2,
                              "strict": False})
            self.assertEqual(receiver.call_count, 1)


class TestAcceptInvite(APITestCase):

    # for now: invites only for admin
    # embed invites in user serialization (?), or make it separate endpoint?
    def test_working_join(self):
        i = InviteFactory.create()

        response = self.client.post(reverse('resturo_organization_join'),
                                    {"token": i.token,
                                     "action": JoinSerializer.JOIN_ACCEPT})

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        # There should be a membership now
        self.assertTrue(Membership.objects.filter(user=i.user,
                                                  organization=i.organization
                                                  ).exists())
        # The invite should be gone
        self.assertEquals(Invite.objects.count(), 0)

    def test_working_reject(self):
        i = InviteFactory.create()

        response = self.client.post(reverse('resturo_organization_join'),
                                    {"token": i.token,
                                     "action": JoinSerializer.JOIN_REJECT})

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        # There shouldn't be a membership now
        self.assertFalse(Membership.objects.filter(user=i.user,
                                                   organization=i.organization
                                                   ).exists())
        # The invite should be gone
        self.assertEquals(Invite.objects.count(), 0)

    def test_user_already_member(self):
        """ invites cannot be used on members or to change roles """
        m = MembershipFactory.create(role=0)
        i = InviteFactory.create(user=m.user, organization=m.organization,
                                 role=1)

        response = self.client.post(reverse('resturo_organization_join'),
                                    {"token": i.token,
                                     "action": JoinSerializer.JOIN_ACCEPT})

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        # There should be only one membership
        self.assertEquals(Membership.objects.filter(user=i.user,
                                                    organization=i.organization
                                                    ).count(), 1)
        # and the role should remain unchanged
        self.assertEquals(Membership.objects.filter(user=i.user,
                                                    organization=i.organization
                                                    ).first().role, 0)
        # The invite is still present
        self.assertEquals(Invite.objects.count(), 1)

    def test_user_already_member_reject(self):
        """ invites cannot be used on members or to change roles.
            The invite can be rejected """
        m = MembershipFactory.create(role=0)
        i = InviteFactory.create(user=m.user, organization=m.organization,
                                 role=1)

        response = self.client.post(reverse('resturo_organization_join'),
                                    {"token": i.token,
                                     "action": JoinSerializer.JOIN_REJECT})

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(Invite.objects.count(), 0)
