from django.contrib.auth.models import User
from rest_framework import generics, response, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

from django.http import Http404

from .permissions import IsStaffOrTargetUser
from .serializers import UserSerializer, UserCreateSerializer, OrganizationSerializer

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
        ## make this serializer more dynamic
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            self.object = serializer.save()
            self.object.is_active = True
            self.object.save()
            ## Do organization magic
            headers = self.get_success_headers(serializer.data)
            return response.Response(serializer.data,
                                     status=status.HTTP_201_CREATED,
                                     headers=headers)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

class OrganizationList(generics.ListCreateAPIView):
    model = None # abstract. Resolve?
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.model.objects.all()
        ## TODO: add role user has in this org
        return self.request.user.organizations.all()


class OrganizationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = None # abstract. Resolve?
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return self.model.objects.all()


class Rommel(object):

    def check_permissions(self, request):
        # allow non-authenticated user to create via POST
        import pdb; pdb.set_trace()
        
        return True
        if self.request.method == "POST":
            return AllowAny()
        return IsStaffOrTargetUser()
