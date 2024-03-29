import pytest   # python -m pytest -v tests
from library import create_app

from library.adapters import memory_repository, repository_populate
# from library.adapters.memory_repository import MemoryRepository
from utils import get_project_root

TEST_DATA_PATH = get_project_root() / "tests" / "data"


@pytest.fixture
def in_memory_repo():
    repo = memory_repository.MemoryRepository()
    database_mode = False
    repository_populate.populate(TEST_DATA_PATH, repo, database_mode)
    return repo


@pytest.fixture
def client():
    my_app = create_app({
        'TESTING': True,                                # Set to True during testing.
        'REPOSITORY': 'memory',
        'TEST_DATA_PATH': TEST_DATA_PATH,               # Path for loading test data into the repository.
        'WTF_CSRF_ENABLED': False                       # test_client will not send a CSRF token, so disable validation.
    })
    return my_app.test_client()


class AuthenticationManager:
    def __init__(self, client):
        self.__client = client

    def login(self, user_name='username', password='Password1'):
        return self.__client.post(
            'authentication/login',
            data={'user_name': user_name, 'password': password}
        )

    def logout(self):
        return self.__client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthenticationManager(client)
