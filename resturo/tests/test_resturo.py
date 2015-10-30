import unittest

from .factories import OrganizationFactory as OrganizationFactoryBase
from .models import Organization


class OrganizationFactory(OrganizationFactoryBase):
    class Meta:
        model = Organization


class TestModels(unittest.TestCase):
    def test_organization(self):
        o = OrganizationFactory.create(name="test")
        o.save()
