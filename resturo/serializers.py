from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from .signals import user_rest_created


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',)
        read_only_fields = ('is_staff', 'is_superuser',
                            'is_active', 'date_joined',)


class UserCreateSerializer(serializers.ModelSerializer):
    jwt_token = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'password', 'jwt_token')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = self.Meta.model(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()

        user_rest_created.send_robust(sender=None, user=user)
        #  XXX should be jwt / token agnostic!

        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.jwt_token = token

        return user


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name")
