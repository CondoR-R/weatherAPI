import pytest
from types import SimpleNamespace
from sqlalchemy.exc import SQLAlchemyError

from src.schemas.users import UsersPostSchema

@pytest.fixture
def mock_select_user(mocker):
    '''
    Фикстура, мокающая функцию select_city в модуле src.api.users.
    '''
    mock = mocker.patch(
        'src.api.users.select_user',
        new_callable=mocker.AsyncMock
    )
    return mock


@pytest.fixture
def mock_insert_user(mocker):
    '''
    Фикстура, мокающая функцию insert_city в модуле src.api.users.
    '''
    mock = mocker.patch(
        'src.api.users.insert_user',
        new_callable=mocker.AsyncMock
    )
    return mock


def test_post_user_success_registration(client, mock_select_user, mock_insert_user):
    '''
    Успешная регистрация пользователя -> 201 и ответ в виде id пользователя
    '''
    mock_select_user.return_value = None
    expected_insert = 42
    mock_insert_user.return_value = expected_insert

    new_user = {'user_name': 'Test'}
    response = client.post('/users', json=new_user)

    assert response.status_code == 201
    assert response.json() == {'id': expected_insert}

    mock_select_user.assert_awaited_once_with(UsersPostSchema(**new_user))
    mock_insert_user.assert_awaited_once_with(UsersPostSchema(**new_user))


def test_post_user_success_authorization(client, mock_select_user, mock_insert_user):
    '''
    Успешная авторизация существующего пользователя -> 200 и ответ в виде id
    '''
    expected_select = SimpleNamespace(id=42, user_name='Test')
    mock_select_user.return_value = expected_select

    user = {'user_name': 'Test'}
    response = client.post('/users', json=user)

    assert response.status_code == 200
    assert response.json() == {'id': expected_select.id}

    mock_select_user.assert_awaited_once_with(UsersPostSchema(**user))
    mock_insert_user.assert_not_awaited()


def test_post_user_without_body(client, mock_select_user, mock_insert_user):
    '''
    Запрос без указания user_name -> 422 с описанием ошибки
    '''
    response = client.post('/users', json={})

    assert response.status_code == 422
    
    detail = response.json()['detail']
    assert any(
        err.get('loc') == ['body', 'user_name'] and err.get('type') == 'missing'
        for err in detail
    )

    mock_select_user.assert_not_awaited()
    mock_insert_user.assert_not_awaited()


def test_post_user_empty_user_name(client, mock_select_user, mock_insert_user):
    '''
    Запрос с пустым user_name -> 422 с описанием ошибки
    '''
    response = client.post('/users', json={'user_name': ''})

    assert response.status_code == 422
    
    detail = response.json()['detail']
    assert detail == 'The user_name field must not be empty.'

    mock_select_user.assert_not_awaited()
    mock_insert_user.assert_not_awaited()


def test_post_user_select_error(client, mock_select_user, mock_insert_user):
    '''
    Корректный запрос, но ошибка со стороны базы данных при поиске пользователя
    -> 500 код.
    '''
    mock_select_user.side_effect = SQLAlchemyError('DB error')
    response = client.post('/users', json={'user_name': 'Test'})
    assert response.status_code == 500


def test_post_user_insert_error(client, mock_select_user, mock_insert_user):
    '''
    Корректный запрос, но ошибка со стороны базы данных при добавлении пользователя
    -> 500 код.
    '''
    mock_select_user.return_value = None
    mock_insert_user.side_effect = SQLAlchemyError('DB error')
    response = client.post('/users', json={'user_name': 'Test'})
    assert response.status_code == 500
