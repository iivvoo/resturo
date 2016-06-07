from django.contrib.auth.models import User
from rest_framework import generics, response, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from django.http import Http404
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

from .serializers import UserSerializer, UserCreateSerializer
from .serializers import PasswordResetSerializer
from .serializers import OrganizationSerializer
from .serializers import InviteSerializer
from .serializers import JoinSerializer

from .signals import user_password_reset, user_rest_created
from .signals import user_password_confirm, user_rest_emailchange
from .signals import user_existing_invite, user_email_invite

from .models import EmailVerification
from .models import modelresolver

from .permissions import OrganizationPermission


class UserCreateView(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    model = User

    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        """
            require username, password, email
            username must be unique
            create organization for username (does not have to be unique)
              with 'admin' role
        """
        #  make this serializer more dynamic
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            self.object = serializer.save()
            self.object.is_active = True
            self.object.save()
            user_rest_created.send_robust(sender=None, user=self.object)
            #  Do organization magic
            headers = self.get_success_headers(serializer.data)
            return response.Response(serializer.data,
                                     status=status.HTTP_201_CREATED,
                                     headers=headers)
        return response.Response(serializer.errors,
                                 status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.model.objects.all()
        else:
            return self.model.objects.filter(id=self.request.user.id)


class UserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    model = User

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.model.objects.all()
        else:
            return self.model.objects.filter(id=self.request.user.id)

    def update(self, request, *args, **kwargs):
        """ Check if email address has changed. If so, fire signal """
        instance_before = self.get_object()
        res = super().update(request, *args, **kwargs)

        if not getattr(settings, "RESTURO_VERIFY_EMAIL", False):
            return res

        instance_after = self.get_object()

        if instance_before.email.strip().lower() != \
           instance_after.email.strip().lower():
            verification, _ = EmailVerification.objects.get_or_create(
                user=instance_after)
            verification.previous = instance_before.email
            verification.reset()
            user_rest_emailchange.send_robust(sender=None, user=instance_after)
        return res


class UserSelfView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self, queryset=None):
        if not self.request.user.is_authenticated():
            raise Http404()
        return self.request.user


class PasswordResetView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """ Find user and fire signal for sending password reset email
            Do not leak "existence" of user by returing anything other
            than a 200 status code
        """
        handle = request.GET.get('handle', '').strip().lower()
        if handle:
            user = User.objects.filter(email=handle).first()
            if not user:
                user = User.objects.filter(username=handle).first()

            if user and user.is_active:
                user_password_reset.send_robust(sender=None, user=user)
        return Response({"status": "ok"})

    def post(self, request, format=None):
        s = PasswordResetSerializer(data=request.data)
        if not s.is_valid():
            return response.Response({"error": "invalid password"},
                                     status=status.HTTP_400_BAD_REQUEST)

        data = s.data
        token = data.get('token', '')
        password = data.get('password', '')

        if not password.strip():
            return response.Response({"non_field_errors":
                                      ["invalid password"]},
                                     status=status.HTTP_400_BAD_REQUEST)

        try:
            uid, token = token.split("-", 1)
            uid = int(uid)
        except ValueError:
            return response.Response({"non_field_errors": ["invalid token"]},
                                     status=status.HTTP_400_BAD_REQUEST)
        user = None
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return response.Response({"non_field_errors": ["invalid token"]},
                                     status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.set_password(password)
            user.save()
            user_password_confirm.send_robust(sender=None, user=user)
            return Response({"status": "ok"})

        return response.Response({"non_field_errors": ["invalid token"]},
                                 status=status.HTTP_400_BAD_REQUEST)


class EmailVerificationView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        """
            Verify email
        """
        token = request.GET.get('token', '').strip().lower()
        if token:
            try:
                verification = EmailVerification.objects.get(token=token)
                if not verification.verified:
                    verification.verified = True
                    verification.save()
                    return Response({"status": "ok"})
            except EmailVerification.DoesNotExist:
                pass
        return response.Response({"non_field_errors": ["invalid token"]},
                                 status=status.HTTP_400_BAD_REQUEST)


class OrganizationList(generics.ListCreateAPIView):
    model = modelresolver.Organization
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.model.objects.all()
        #  TODO: add role user has in this org
        return self.request.user.organizations.all()


class OrganizationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = modelresolver("Organization")
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return self.model.objects.all()


class OrganizationInvite(generics.CreateAPIView):
    model = modelresolver("Organization")
    serializer_class = InviteSerializer
    permission_classes = (IsAuthenticated, OrganizationPermission)

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.model.objects.all()
        return self.model.objects.all()

    def create(self, request, *args, **kwargs):
        """ create, accept or reject an invite """
        org = self.get_object()
        deserialized = self.serializer_class(data=request.data)

        if not deserialized.is_valid():
            return response.Response(
                deserialized.errors,
                status=status.HTTP_400_BAD_REQUEST)

        data = deserialized.data

        handle = data.get('handle', None)
        email = handle if '@' in handle else ""
        role = data.get('role', 0)
        strict = data.get('strict', False)

        user = User.objects.filter(email=handle).first()
        if not user:
            user = User.objects.filter(username=handle).first()

        if user:
            if org in user.organizations.all():
                return response.Response(
                    {"non_field_errors": ["User is already member"]},
                    status=status.HTTP_400_BAD_REQUEST)
        elif not email:
            return response.Response(
                {"handle": ["Does not match user or existing email"]},
                status=status.HTTP_400_BAD_REQUEST)

        invite = modelresolver('Invite')(user=user, inviter=self.request.user,
                                         email=email,
                                         role=role, strict=strict,
                                         organization=org)
        invite.save()

        # At this point we have a valid user or a somewhat valid email.
        # Fire signal so email can be sent

        if user and user.is_active:
            user_existing_invite.send_robust(sender=org, invite=invite)
        else:  # must be email
            user_email_invite.send_robust(sender=org, invite=invite)
        return Response({"status": "ok"})


class OrganizationJoin(APIView):
    serializer_class = JoinSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.model.objects.all()
        return self.model.objects.all()

    def post(self, request, *args, **kwargs):
        """ create, accept or reject an invite """
        deserialized = self.serializer_class(data=request.data)

        if not deserialized.is_valid():
            return response.Response(
                deserialized.errors,
                status=status.HTTP_400_BAD_REQUEST)

        data = deserialized.data

        inviteclass = modelresolver('Invite')
        membershipclass = modelresolver('Membership')

        try:
            invite = inviteclass.objects.get(token=data['token'])
        except inviteclass.DoesNotExist:
            raise Http404()

        if data['action'] == self.serializer_class.JOIN_ACCEPT:
            m, c = membershipclass.objects.get_or_create(
                user=self.request.user,
                organization=invite.organization)
            if not c:
                return response.Response(
                    {"non_field_errors": ["User is already member"]},
                    status=status.HTTP_400_BAD_REQUEST)
            m.role = invite.role
            m.save()

        invite.delete()
        return Response({"status": "ok"})
