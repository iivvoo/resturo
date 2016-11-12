import pytest

from .factories import UserFactory, user_with_org


@pytest.fixture
def user(request):
    return UserFactory.create()


@pytest.fixture
def alice(request):
    return UserFactory.create(username="alice")


@pytest.fixture
def bob(request):
    return UserFactory.create(username="bob")


@pytest.fixture
def user_wo(request):
    return user_with_org("johndoe", "Doe Inc.")


@pytest.fixture
def alice_wo(request):
    return user_with_org("alice", "Alice Inc.")


@pytest.fixture
def bob_wo(request):
    return user_with_org("bob", "Bob Inc.")
