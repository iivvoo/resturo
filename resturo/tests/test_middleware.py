from django.test import TestCase, RequestFactory
from django.core.exceptions import PermissionDenied

from .factories import UserFactory, OrganizationFactory
from .factories import user_with_org
from ..middleware import SelectOrganizationMiddleware

from .models import Membership


class TestSelectOrganizationMiddleware(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.jane, self.jane_org = user_with_org('jane', 'emac')
        self.john, self.john_org = user_with_org('john', 'acme')
        self.superuser = UserFactory.create(username='superuser',
                                            is_superuser=True)

    def test_missing_header_anon(self):
        """ anonymous and no header means no organization """
        req = self.factory.get('/', {})
        mw = SelectOrganizationMiddleware()
        mw.process_request(req)
        self.assertRaises(AttributeError, lambda: req.organization)

    def test_anon_no_access(self):
        """ anonymous user can't set organization """
        req = self.factory.get('/', {}, HTTP_ORGANIZATION=self.john_org.id)
        mw = SelectOrganizationMiddleware()
        mw.process_request(req)
        self.assertRaises(AttributeError, lambda: req.organization)

    def test_missing_header_default(self):
        """ a user with organization will default to latest organization if
            no header provided """
        req = self.factory.get('/', {})
        req.user = self.john
        mw = SelectOrganizationMiddleware()
        mw.process_request(req)
        self.assertEquals(req.organization, self.john_org)

    def test_missing_header_default_latest(self):
        """ a user with organization will default to latest organization if
            no header provided """
        neworg = OrganizationFactory.create()
        Membership.objects.create(organization=neworg, user=self.john)

        req = self.factory.get('/', {})
        req.user = self.john
        mw = SelectOrganizationMiddleware()
        mw.process_request(req)
        self.assertEquals(req.organization, neworg)

    def test_incorrect_id(self):
        """ Non-existing id's are handled gracefully """
        req = self.factory.get('/', {}, HTTP_ORGANIZATION=1234)
        req.user = self.john
        mw = SelectOrganizationMiddleware()
        mw.process_request(req)
        self.assertRaises(AttributeError, lambda: req.organization)

    def test_simple(self):
        """ most trivial working case """
        req = self.factory.get('/', {}, HTTP_ORGANIZATION=self.john_org.id)
        req.user = self.john
        mw = SelectOrganizationMiddleware()
        mw.process_request(req)
        self.assertEquals(req.organization, self.john_org)

    def test_not_member(self):
        """ only access to organization the user is member of """
        req = self.factory.get('/', {}, HTTP_ORGANIZATION=self.john_org.id)
        req.user = self.jane
        mw = SelectOrganizationMiddleware()
        with self.assertRaises(PermissionDenied):
            mw.process_request(req)

    def test_superuser_access(self):
        """ superuser can do anything """
        req = self.factory.get('/', {}, HTTP_ORGANIZATION=self.john_org.id)
        req.user = self.superuser
        mw = SelectOrganizationMiddleware()
        mw.process_request(req)
        self.assertEquals(req.organization, self.john_org)

    def test_handle_invalid_token(self):
        req = self.factory.get('/', {},
                               HTTP_ORGANIZATION=self.john_org.id,
                               HTTP_AUTHORIZATION="JWT not-a-valid-token")
        mw = SelectOrganizationMiddleware()
        with self.assertRaises(PermissionDenied):
            mw.process_request(req)
