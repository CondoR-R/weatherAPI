import pytest
from fastapi.testclient import TestClient

from src.main import app

@pytest.fixture(scope='session')
def client():
    '''
    Фикстура, создающая тестовый клиент для всего сеанса тестирования.
    Используется во всех тестах без явного импорта.
    '''
    with TestClient(app) as c:
        yield c

