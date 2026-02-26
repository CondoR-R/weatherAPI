import pytest
from types import SimpleNamespace
from sqlalchemy.exc import SQLAlchemyError
import httpx

# Фикстура с данными города для переиспользования
@pytest.fixture
def city_data():
    return {
        'city': 'Москва',
        'user_id': 1,
        'lat': 55.75,
        'lon': 37.62
    }


@pytest.fixture
def post_city_mocks(mocker):
    '''
    Фикстура с моками функций в модуле src.api.cities в функции post_city.
    '''
    return SimpleNamespace(
        check_user = mocker.patch(
            'src.api.cities.check_user', 
            new_callable=mocker.AsyncMock
        ),
        get_new_city_hourly_weather = mocker.patch(
            'src.api.cities.get_new_city_hourly_weather',
            new_callable=mocker.AsyncMock
        ),
        insert_city = mocker.patch(
            'src.api.cities.insert_city',
            new_callable=mocker.AsyncMock
        ),
        hourly_weather_formation = mocker.patch(
            'src.api.cities.hourly_weather_formation',
        ),
        insert_weather = mocker.patch(
            'src.api.cities.insert_weather',
            new_callable=mocker.AsyncMock
        )
    )


def test_post_city_success(client, post_city_mocks, city_data):
    '''
    Успешное добавление города -> 201 код
    '''
    post_city_mocks.check_user.return_value = None
    post_city_mocks.get_new_city_hourly_weather.return_value = (
        {'mock': 'data'}, 0
    )
    post_city_mocks.insert_city.return_value = 1
    post_city_mocks.hourly_weather_formation.return_value = []
    post_city_mocks.insert_weather.return_value = None

    response = client.post(
        '/cities', 
        json=city_data
    )

    assert response.status_code == 201
    assert response.json() == {'detail': 'City ​​added successfully'}

    # Проверяем вызовы
    post_city_mocks.check_user.assert_called_once_with(1)
    post_city_mocks.get_new_city_hourly_weather.assert_called_once()
    post_city_mocks.insert_city.assert_called_once()
    post_city_mocks.hourly_weather_formation.assert_called_once()
    post_city_mocks.insert_weather.assert_called_once()


def test_post_city_check_user_err(client, post_city_mocks, city_data):
    '''
    Ошибка при проверке пользователя (check_user) со стороны базы данных
    -> 500 код
    '''
    post_city_mocks.check_user.side_effect = SQLAlchemyError('DB error')

    respone = client.post('/cities', json=city_data)

    assert respone.status_code == 500

    # Проверяем, что дальнейшие функции не вызывались
    post_city_mocks.get_new_city_hourly_weather.assert_not_called()
    post_city_mocks.insert_city.assert_not_called()
    post_city_mocks.hourly_weather_formation.assert_not_called()
    post_city_mocks.insert_weather.assert_not_called()


def test_post_city_http_error(client, post_city_mocks, city_data):
    '''
    Ошибка со стороны Open Meteo API (например перегружены сервера) 
    -> 503 код с сообщением об ошибке
    '''
    post_city_mocks.check_user.return_value = None

    error_response = httpx.Response(503, json={'error': 'Service Unavailable'})
    post_city_mocks.get_new_city_hourly_weather.side_effect = httpx.HTTPStatusError(
        'Error',
        request=httpx.Request('GET', 'url'),
        response=error_response
    )

    response = client.post('/cities', json=city_data)

    assert response.status_code == 503
    assert 'Open Meteo API' in response.json()['detail']

    post_city_mocks.check_user.assert_called_once_with(1)
    # Дальнейшие функции не вызываются
    post_city_mocks.insert_city.assert_not_called()
    post_city_mocks.hourly_weather_formation.assert_not_called()
    post_city_mocks.insert_weather.assert_not_called()


def test_post_city_timeout(client, post_city_mocks, city_data):
    '''
    Таймаут при обращении Open Meteo API -> 504 ошибка.
    '''
    post_city_mocks.check_user.return_value = None
    post_city_mocks.get_new_city_hourly_weather.side_effect = httpx.TimeoutException('Timeout')

    response = client.post('/cities', json=city_data)

    assert response.status_code == 504
    assert ('The city has been successfully added! However, when attempting to retrieve the hourly weather forecast for the city, the Open Meteo API timed out.' 
    in response.json()['detail'])

    post_city_mocks.check_user.assert_called_once_with(1)
    post_city_mocks.insert_city.assert_not_called()
    post_city_mocks.hourly_weather_formation.assert_not_called()
    post_city_mocks.insert_weather.assert_not_called()


def test_post_city_conflict(client, post_city_mocks, city_data):
    '''
    При добавлении города город уже есть в базе данных -> 409 с сообщением
    '''
    post_city_mocks.check_user.return_value = None
    post_city_mocks.get_new_city_hourly_weather.return_value = (
        {'mock': 'data'}, 0
    )
    post_city_mocks.insert_city.side_effect = ValueError()

    response = client.post('/cities', json=city_data)

    assert response.status_code == 409
    assert 'City already exists for this user' in response.json()['detail']

    post_city_mocks.check_user.assert_called_once_with(1)
    post_city_mocks.get_new_city_hourly_weather.assert_called_once()
    post_city_mocks.insert_city.assert_called_once()
    post_city_mocks.hourly_weather_formation.assert_not_called()
    post_city_mocks.insert_weather.assert_not_called()


def test_post_city_insert_city_err(client, post_city_mocks, city_data):
    '''
    Ошибка базы данных при вставке города -> 500 код
    '''
    post_city_mocks.check_user.return_value = None
    post_city_mocks.get_new_city_hourly_weather.return_value = (
        {'mock': 'data'}, 0
    )
    post_city_mocks.insert_city.side_effect = SQLAlchemyError('DB error')

    respose = client.post('/cities', json=city_data)

    assert respose.status_code == 500

    post_city_mocks.check_user.assert_called_once_with(1)
    post_city_mocks.get_new_city_hourly_weather.assert_called_once()
    post_city_mocks.insert_city.assert_called_once()
    post_city_mocks.hourly_weather_formation.assert_not_called()
    post_city_mocks.insert_weather.assert_not_called()


def test_post_city_insert_weather_err(client, post_city_mocks, city_data):
    '''
    Ошибка базы данных при вставке погоды -> 500 код
    '''
    post_city_mocks.check_user.return_value = None
    post_city_mocks.get_new_city_hourly_weather.return_value = (
        {'mock': 'data'}, 0
    )
    post_city_mocks.insert_city.return_value = 1
    post_city_mocks.hourly_weather_formation.return_value = []
    post_city_mocks.insert_weather.side_effect = SQLAlchemyError('DB error')

    respose = client.post('/cities', json=city_data)

    assert respose.status_code == 500

    post_city_mocks.check_user.assert_called_once_with(1)
    post_city_mocks.get_new_city_hourly_weather.assert_called_once()
    post_city_mocks.insert_city.assert_called_once()
    post_city_mocks.hourly_weather_formation.assert_called_once()
    post_city_mocks.insert_weather.assert_called_once()  # вызывалась, но упала


def test_post_city_incorrect_data(client, post_city_mocks):
    '''
    Некорректные входные данные -> 422 код
    '''
    bad_data = {
        'city': 1,           # должно быть строкой
        'user_id': '1',      # должно быть int
        'lat': '55.75',      # должно быть float
        'lon': '37.62'       # должно быть float
    }
    response = client.post(
        '/cities', 
        json=bad_data
    )
    
    assert response.status_code == 422

    post_city_mocks.check_user.assert_not_called()
    post_city_mocks.get_new_city_hourly_weather.assert_not_called()
    post_city_mocks.insert_city.assert_not_called()
    post_city_mocks.hourly_weather_formation.assert_not_called()
    post_city_mocks.insert_weather.assert_not_called()
