from twotest.quicktest import QuickDjangoTest

if __name__ == '__main__':
    QuickDjangoTest(
        apps=(
            'django.contrib.auth',
            "resturo",
        ),
        installed_apps=(
            'twotest',
        ),
        ROOT_URLCONF="",
        USE_TZ=True,
        STATIC_URL='/'
    )
