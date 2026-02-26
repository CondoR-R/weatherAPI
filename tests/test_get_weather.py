import pytest
from sqlalchemy.exc import SQLAlchemyError
from types import SimpleNamespace

from src.schemas.hourly_weather import ParamsEnum

@pytest.fixture
def weather_query_mocks(mocker):
    '''
    Фикстура с моками функций в модуле src.api.hourly.weather в функции get_weather.
    '''
    return SimpleNamespace(
        check_user=mocker.patch(
            'src.api.hourly_weather.check_user',
            new_callable=mocker.AsyncMock
        ),
        select_city=mocker.patch(
            'src.api.hourly_weather.select_city',
            new_callable=mocker.AsyncMock
        ),
        select_weather=mocker.patch(
            'src.api.hourly_weather.select_weather',
            new_callable=mocker.AsyncMock
        ),
        set_time=mocker.patch(
            'src.api.hourly_weather.set_time',
            return_value='2025-02-26 15:00:00'  # фиксированное время для предсказуемости
        )
    )


@pytest.fixture
def mock_city():
    '''Возвращает объект города с необходимыми атрибутами.'''
    class City:
        id = 1
        timezone = 0
    return City()


@pytest.fixture
def mock_weather():
    '''Возвращает объект погоды с методом model_dump.'''
    class Weather:
        def __init__(self, **kwargs):
            self.temperature = kwargs.get('temperature', -5.0)
            self.relative_humidity = kwargs.get('relative_humidity', 80)
            self.wind_speed = kwargs.get('wind_speed', 3.5)
            self.precipitation = kwargs.get('precipitation', 0.2)

        def model_dump(self):
            return {
                'temperature': self.temperature,
                'relative_humidity': self.relative_humidity,
                'wind_speed': self.wind_speed,
                'precipitation': self.precipitation
            }
    return Weather()


def test_get_weather_success_all_params(client, weather_query_mocks, mock_city, mock_weather):
    '''
    Успешный запрос без указания params (или с params, содержащим все параметры).
    -> 200 и полный словарь погоды.
    '''
    user_id = 1
    city_name = 'Moscow'
    time = 15

    weather_query_mocks.check_user.return_value = None
    weather_query_mocks.select_city.return_value = mock_city
    weather_query_mocks.select_weather.return_value = mock_weather

    response = client.get(
        f'/weather?user_id={user_id}&city={city_name}&time={time}'
    )

    assert response.status_code == 200

    assert response.json() == mock_weather.model_dump()

    # Проверяем вызовы
    weather_query_mocks.check_user.assert_awaited_once_with(user_id)
    weather_query_mocks.select_city.assert_awaited_once_with(city_name, user_id)
    # set_time вызван с (time, mock_city.timezone)
    weather_query_mocks.set_time.assert_called_once_with(time, mock_city.timezone)
    weather_query_mocks.select_weather.assert_awaited_once_with(mock_city.id, weather_query_mocks.set_time.return_value)


def test_get_weather_success_selected_params(client, weather_query_mocks, mock_city, mock_weather):
    '''
    Успешный запрос с указанием конкретных параметров через запятую. ->
    200 и словарь только с запрошенными параметрами.
    '''
    user_id = 1
    city_name = 'Moscow'
    time = 15
    params = 'temperature,wind_speed'

    weather_query_mocks.check_user.return_value = None
    weather_query_mocks.select_city.return_value = mock_city
    weather_query_mocks.select_weather.return_value = mock_weather

    response = client.get(
        f'/weather?user_id={user_id}&city={city_name}&time={time}&params={params}'
    )

    assert response.status_code == 200
    expected = {
        'temperature': mock_weather.temperature,
        'wind_speed': mock_weather.wind_speed
    }
    assert response.json() == expected

    weather_query_mocks.check_user.assert_awaited_once_with(user_id)
    weather_query_mocks.select_city.assert_awaited_once_with(city_name, user_id)
    weather_query_mocks.set_time.assert_called_once_with(time, mock_city.timezone)
    weather_query_mocks.select_weather.assert_awaited_once_with(mock_city.id, weather_query_mocks.set_time.return_value)


def test_get_weather_check_user_db_error(client, weather_query_mocks):
    '''
    Ошибка базы данных при проверке пользователя (check_user) -> 500.
    '''
    user_id = 1
    city_name = 'Moscow'
    time = 15

    weather_query_mocks.check_user.side_effect = SQLAlchemyError('DB error')

    response = client.get(f'/weather?user_id={user_id}&city={city_name}&time={time}')

    assert response.status_code == 500
    assert response.json()['detail'] == 'Internal server error'

    weather_query_mocks.check_user.assert_awaited_once_with(user_id)
    weather_query_mocks.select_city.assert_not_called()
    weather_query_mocks.select_weather.assert_not_called()


def test_get_weather_params_with_spaces(client, weather_query_mocks):
    '''
    Параметр params содержит пробелы (разделитель – пробел) -> 400.
    '''
    user_id = 1
    city_name = 'Moscow'
    time = 15
    params = 'temperature wind_speed'  # пробел вместо запятой

    response = client.get(
        f'/weather?user_id={user_id}&city={city_name}&time={time}&params={params}'
    )

    assert response.status_code == 400
    assert 'Parameters must be written without spaces' in response.json()['detail']

    weather_query_mocks.check_user.assert_awaited_once_with(user_id)
    weather_query_mocks.select_city.assert_not_called()
    weather_query_mocks.select_weather.assert_not_called()


def test_get_weather_invalid_param(client, weather_query_mocks):
    '''
    В params передан несуществующий параметр -> 400 код.
    '''
    user_id = 1
    city_name = 'Moscow'
    time = 15
    params = 'temperature,invalid_param'

    response = client.get(
        f'/weather?user_id={user_id}&city={city_name}&time={time}&params={params}'
    )

    assert response.status_code == 400
    error_detail = response.json()['detail']
    assert 'invalid_param is not a valid parameter' in error_detail
    for p in ParamsEnum:
        assert p.value in error_detail

    weather_query_mocks.check_user.assert_awaited_once_with(user_id)
    weather_query_mocks.select_city.assert_not_called()
    weather_query_mocks.select_weather.assert_not_called()


def test_get_weather_select_city_db_error(client, weather_query_mocks):
    '''
    Ошибка БД при select_city -> 500.
    '''
    user_id = 1
    city_name = 'Moscow'
    time = 15

    weather_query_mocks.check_user.return_value = None
    weather_query_mocks.select_city.side_effect = SQLAlchemyError('DB error')

    response = client.get(f'/weather?user_id={user_id}&city={city_name}&time={time}')

    assert response.status_code == 500
    assert response.json()['detail'] == 'Internal server error'

    weather_query_mocks.check_user.assert_awaited_once_with(user_id)
    weather_query_mocks.select_city.assert_awaited_once_with(city_name, user_id)
    weather_query_mocks.select_weather.assert_not_called()


def test_get_weather_city_not_found(client, weather_query_mocks):
    '''
    Город не найден в БД для данного пользователя -> 404.
    '''
    user_id = 1
    city_name = 'NonExistentCity'
    time = 15

    weather_query_mocks.check_user.return_value = None
    weather_query_mocks.select_city.return_value = None  # город не найден

    response = client.get(f'/weather?user_id={user_id}&city={city_name}&time={time}')

    assert response.status_code == 404
    assert f'City {city_name} was not found' in response.json()['detail']

    weather_query_mocks.check_user.assert_awaited_once_with(user_id)
    weather_query_mocks.select_city.assert_awaited_once_with(city_name, user_id)
    weather_query_mocks.select_weather.assert_not_called()


def test_get_weather_select_weather_db_error(client, weather_query_mocks, mock_city):
    '''
    Ошибка БД при select_weather -> 500.
    '''
    user_id = 1
    city_name = 'Moscow'
    time = 15

    weather_query_mocks.check_user.return_value = None
    weather_query_mocks.select_city.return_value = mock_city
    weather_query_mocks.select_weather.side_effect = SQLAlchemyError('DB error')

    response = client.get(f'/weather?user_id={user_id}&city={city_name}&time={time}')

    assert response.status_code == 500
    assert response.json()['detail'] == 'Internal server error'

    weather_query_mocks.check_user.assert_awaited_once_with(user_id)
    weather_query_mocks.select_city.assert_awaited_once_with(city_name, user_id)
    weather_query_mocks.select_weather.assert_awaited_once_with(mock_city.id, weather_query_mocks.set_time.return_value)


def test_get_weather_missing_user_id(client, weather_query_mocks):
    '''
    Запрос без обязательного параметра user_id -> 422.
    '''
    response = client.get('/weather?city=Moscow&time=15')

    assert response.status_code == 422
    detail = response.json()['detail']
    assert any(
        err.get('loc') == ['query', 'user_id'] and err.get('type') == 'missing'
        for err in detail
    )

    weather_query_mocks.check_user.assert_not_called()


def test_get_weather_missing_city(client, weather_query_mocks):
    '''
    Запрос без обязательного параметра city -> 422.
    '''
    response = client.get('/weather?user_id=1&time=15')

    assert response.status_code == 422
    detail = response.json()['detail']
    assert any(
        err.get('loc') == ['query', 'city'] and err.get('type') == 'missing'
        for err in detail
    )

    weather_query_mocks.check_user.assert_not_called()


def test_get_weather_missing_time(client, weather_query_mocks):
    '''
    Запрос без обязательного параметра time -> 422.
    '''
    response = client.get('/weather?user_id=1&city=Moscow')

    assert response.status_code == 422
    detail = response.json()['detail']
    assert any(
        err.get('loc') == ['query', 'time'] and err.get('type') == 'missing'
        for err in detail
    )

    weather_query_mocks.check_user.assert_not_called()


def test_get_weather_invalid_user_id_type(client, weather_query_mocks):
    '''
    user_id передан строкой, не являющейся числом -> 422.
    '''
    response = client.get('/weather?user_id=abc&city=Moscow&time=15')

    assert response.status_code == 422
    detail = response.json()['detail']
    assert any(
        err.get('loc') == ['query', 'user_id'] and err.get('type') == 'int_parsing'
        for err in detail
    )

    weather_query_mocks.check_user.assert_not_called()


def test_get_weather_invalid_time_type(client, weather_query_mocks):
    '''
    time передан строкой, не являющейся числом -> 422.
    '''
    response = client.get('/weather?user_id=1&city=Moscow&time=abc')

    assert response.status_code == 422
    detail = response.json()['detail']
    assert any(
        err.get('loc') == ['query', 'time'] and err.get('type') == 'int_parsing'
        for err in detail
    )

    weather_query_mocks.check_user.assert_not_called()


def test_get_weather_time_out_of_range(client, weather_query_mocks):
    '''
    time вне допустимого диапазона 0-23 -> 422.
    '''
    response = client.get('/weather?user_id=1&city=Moscow&time=24')

    assert response.status_code == 422

    weather_query_mocks.check_user.assert_not_called()
