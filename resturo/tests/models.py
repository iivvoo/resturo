from ..models import Organization as BaseOrganization
from ..models import Membership as BaseMembership
from ..models import Invite as BaseInvite


class Organization(BaseOrganization):
    """
    """


class Membership(BaseMembership):
    """ Provide non-abstract implementation for Membership model,
        define some roles
    """
    ROLE_MEMBER = 1


class Invite(BaseInvite):
    """ """
