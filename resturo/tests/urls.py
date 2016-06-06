from django.conf.urls import url, patterns, include

import resturo.urls

urlpatterns = patterns(
    '',
    url(r'^users/', include(resturo.urls.user_patterns)),
    url(r'^organizations/', include(resturo.urls.organizations_patterns)),
)
