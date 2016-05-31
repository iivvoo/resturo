from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(
    '',
    url(r'^$', views.UserCreateView.as_view(), name='resturo_user_create'),
    url(r'self', views.UserSelfView.as_view(), name='resturo_user_self'),
    url(r'reset', views.PasswordResetView.as_view(),
        name='resturo_user_reset'),
    url(r'verify', views.EmailVerificationView.as_view(),
        name='resturo_user_verify'),
    url(r'^(?P<pk>[0-9]+)/$',
        views.UserDetailView.as_view(),
        name='resturo_user_detail')
)
