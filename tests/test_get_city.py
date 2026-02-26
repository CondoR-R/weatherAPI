import pytest
from sqlalchemy.exc import SQLAlchemyError
from types import SimpleNamespace

@pytest.fixture
def get_cities_mocks(mocker):
    '''
    Фикстура с моками функций в модуле src.api.cities в функции get_city.
    '''
    return SimpleNamespace(
        check_user=mocker.patch(
            'src.api.cities.check_user',
            new_callable=mocker.AsyncMock
        ),
        select_cities=mocker.patch(
            'src.api.cities.select_cities',
            new_callable=mocker.AsyncMock
        )
    )


def test_get_cities_success(client, get_cities_mocks):
    '''
    Успешное получение списка городов для существующего пользователя ->
    200 код и список названий городов.
    '''
    user_id = 42
    expected_cities = ['Москва', 'Санкт-Петербург', 'Казань']

    get_cities_mocks.check_user.return_value = None
    get_cities_mocks.select_cities.return_value = expected_cities

    response = client.get(f'/cities?user_id={user_id}')

    assert response.status_code == 200
    assert response.json() == expected_cities

    get_cities_mocks.check_user.assert_awaited_once_with(user_id)
    get_cities_mocks.select_cities.assert_awaited_once_with(user_id)


def test_get_cities_empty_list(client, get_cities_mocks):
    '''
    Пользователь существует, но у него нет отслеживаемых городов ->
    200 и пустой список.
    '''
    user_id = 99
    get_cities_mocks.check_user.return_value = None
    get_cities_mocks.select_cities.return_value = []

    response = client.get(f'/cities?user_id={user_id}')

    assert response.status_code == 200
    assert response.json() == []

    get_cities_mocks.check_user.assert_awaited_once_with(user_id)
    get_cities_mocks.select_cities.assert_awaited_once_with(user_id)


def test_get_cities_missing_user_id(client, get_cities_mocks):
    '''
    Запрос без обязательного параметра user_id -> 422 код.
    '''
    response = client.get('/cities')

    assert response.status_code == 422
    
    detail = response.json()['detail']
    assert any(
        err.get('loc') == ['query', 'user_id'] and err.get('type') == 'missing'
        for err in detail
    )

    get_cities_mocks.check_user.assert_not_called()
    get_cities_mocks.select_cities.assert_not_called()


def test_get_cities_invalid_user_id_type(client, get_cities_mocks):
    '''
    Передан user_id нечислового типа -> 422 код.
    '''
    response = client.get('/cities?user_id=abc')

    assert response.status_code == 422
    detail = response.json()['detail']
    assert any(
        err.get('loc') == ['query', 'user_id'] and err.get('type') == 'int_parsing'
        for err in detail
    )

    get_cities_mocks.check_user.assert_not_called()
    get_cities_mocks.select_cities.assert_not_called()


def test_get_cities_check_user_db_error(client, get_cities_mocks):
    '''
    Ошибка базы данных при проверке существования пользователя (check_user). ->
    500 код.
    '''
    user_id = 1
    get_cities_mocks.check_user.side_effect = SQLAlchemyError('DB error')

    response = client.get(f'/cities?user_id={user_id}')

    assert response.status_code == 500
    assert response.json()['detail'] == 'Internal server error'

    get_cities_mocks.check_user.assert_awaited_once_with(user_id)
    get_cities_mocks.select_cities.assert_not_called()


def test_get_cities_select_cities_db_error(client, get_cities_mocks):
    '''
    Ошибка базы данных при получении списка городов (select_cities). ->
    500 код.
    '''
    user_id = 1
    get_cities_mocks.check_user.return_value = None
    get_cities_mocks.select_cities.side_effect = SQLAlchemyError('DB error')

    response = client.get(f'/cities?user_id={user_id}')

    assert response.status_code == 500
    assert response.json()['detail'] == 'Internal server error'

    get_cities_mocks.check_user.assert_awaited_once_with(user_id)
    get_cities_mocks.select_cities.assert_awaited_once_with(user_id)
