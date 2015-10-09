from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'self', views.UserSelfView.as_view(), name='resturo_user_self'),
    url(r'', views.UserCreateView.as_view(), name='resturo_user_create'),
)
