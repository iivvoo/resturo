from ..models import Organization as BaseOrganization
from ..models import Membership as BaseMembership


class Organization(BaseOrganization):
    """
    """


class Membership(BaseMembership):
    """ Provide non-abstract implementation for Membership model,
        define some roles
    """
    ROLE_MEMBER = 1

