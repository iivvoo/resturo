import unittest

from django.contrib.auth.models import User

from django.core.urlresolvers import reverse
from rest_framework import status

from rest_framework.test import APITestCase
from mock_django.signals import mock_signal_receiver

from .factories import OrganizationFactory as OrganizationFactoryBase
from .factories import UserFactory
from .models import Organization, Invite
from resturo.models import EmailVerification

from resturo.signals import user_password_reset, user_rest_created


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


class TestInvite(APITestCase):

    def test_simple(self):
        o = OrganizationFactory.create()

        response = self.client.put(reverse('resturo_organization_invite',
                                           kwargs={'pk': o.pk}),
                                   {"handle": "test@example.com",
                                    "role": 2,
                                    "strict": False})

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(Invite.objects.count(), 1)
        self.assertEquals(Invite.objects.first().organization, o)
