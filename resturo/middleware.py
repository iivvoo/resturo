from rest_framework.request import Request

from django.core.exceptions import PermissionDenied

from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import modelresolver


def get_user_jwt(request):
    user = None

    try:
        user = request.user

        if user.is_authenticated():
            return user
    except AttributeError:
        pass

    try:
        user_jwt = JSONWebTokenAuthentication().authenticate(Request(request))
    except AuthenticationFailed:
        raise PermissionDenied

    if user_jwt is not None:
        return user_jwt[0]
    return user


class SelectOrganizationMiddleware(object):

    def process_request(self, request):
        """
            Find and set the organization for the current user based on
            the Organization:-header.

            Users can only set an organizations they have access to (unless
            they are superuser). If no header is found, predictably set the
            organization to one the user belongs to.
        """
        Organization = modelresolver("Organization")
        Membership = modelresolver("Membership")

        user = get_user_jwt(request)
        if not user or user.is_anonymous():
            return

        organizationid = request.META.get('HTTP_ORGANIZATION')

        if organizationid and organizationid != 'null':
            try:
                organizationid = int(organizationid)
                organization = Organization.objects.get(
                    pk=organizationid)
                if not (user.is_superuser or
                        Membership.objects.filter(
                        organization__id=organizationid,
                            user=user).exists()):
                    raise PermissionDenied(
                        "You are not part of that organization")
                request.organization = organization
            except ValueError:
                pass
            except Organization.DoesNotExist:
                pass
        else:
            try:
                request.organization = user.organizations.latest('pk')
            except Organization.DoesNotExist:
                pass
