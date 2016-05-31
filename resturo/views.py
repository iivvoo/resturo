from django.contrib.auth.models import User
from rest_framework import generics, response, status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from django.http import Http404
from django.contrib.auth.tokens import default_token_generator

from .serializers import UserSerializer, UserCreateSerializer
from .serializers import PasswordResetSerializer
from .signals import user_password_reset, user_rest_created
from .signals import user_password_confirm
from .models import EmailVerification


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
            verification = EmailVerification.objects.get(token=token)
            if not verification.verified:
                verification.verified = True
                verification.save()
                # user_password_reset.send_robust(sender=None, user=user)
                return Response({"status": "ok"})
        return response.Response({"non_field_errors": ["invalid token"]},
                                 status=status.HTTP_400_BAD_REQUEST)


class OrganizationList(generics.ListCreateAPIView):
    model = None  # abstract. Resolve?
    serializer_class = None

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.model.objects.all()
        #  TODO: add role user has in this org
        return self.request.user.organizations.all()


class OrganizationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = None  # abstract. Resolve?
    serializer_class = None

    def get_queryset(self):
        return self.model.objects.all()
