import pytest
import httpx

from src.schemas.coords import CoordsSchema

@pytest.fixture
def mock_get_current(mocker):
    '''
    Фикстура мокающая функцию get_current в модуле src.api.current_weather.
    '''
    mock = mocker.patch(
        'src.api.current_weather.get_current', 
        new_callable=mocker.AsyncMock
    )
    return mock


def assert_validation_error(response, expected_errors):
    '''
    Проверяет, что ответ содержит 422 и указанные ошибки валидации.
    '''
    assert response.status_code == 422

    detail = response.json()['detail']
    assert len(detail) == len(expected_errors)

    error_dict = {err['loc'][-1]: err['type'] for err in detail}
    assert error_dict == expected_errors


def test_get_current_weather_success(client, mock_get_current):
    '''
    Запрос с правильным форматом координат -> 200 код с ответом в виде погоды.
    '''
    expected_data = {
        'current_temperature': -20.35,
        'current_wind_speed': 5.0,
        'atmospheric_pressure': 1011.0
    }
    mock_get_current.return_value = expected_data

    lat = 56.5
    lon = 85.0
    response = client.get(f'/current_weather?lat={lat}&lon={lon}')

    assert response.status_code == 200
    assert response.json() == expected_data

    # Проверяем, что функция вызвана с правильными координатами один раз
    mock_get_current.assert_awaited_once_with(CoordsSchema(lat=lat, lon=lon))


def test_get_current_weather_without_coords(client):
    '''
    Запрос без lat и lon -> 422 с ошибками по обоим полям.
    '''
    response = client.get('/current_weather')
    assert_validation_error(response, {'lat': 'missing', 'lon': 'missing'})


def test_get_current_weather_without_lat(client):
    '''
    Запрос без указания широты (lat) -> 422 с ошибкой по lat.
    '''
    response = client.get('/current_weather?lon=0')
    assert_validation_error(response, {'lat': 'missing'})


def test_get_current_weather_without_lon(client):
    '''
    Запрос без указания долготы (lon) -> 422 с ошибкой по lon.
    '''
    response = client.get('/current_weather?lat=0')
    assert_validation_error(response, {'lon': 'missing'})


def test_get_current_weather_incorrect_coords(client):
    '''
    Запрос при неправильном типе координат -> 422 с ошибками по обоим полям.
    '''
    response = client.get('/current_weather?lat=a&lon=a')
    assert_validation_error(response, {'lat': 'float_parsing', 'lon': 'float_parsing'})


def test_get_current_weather_incorrect_lat(client):
    '''
    Запрос при неправильном типе долготы (lat) -> 422 с ошибкой по lat.
    '''
    response = client.get('/current_weather?lat=a&lon=0')
    assert_validation_error(response, {'lat': 'float_parsing'})


def test_get_current_weather_incorrect_lon(client):
    '''
    Запрос при неправильном типе широты (lon) -> 422 с ошибкой по lon.
    '''
    response = client.get('/current_weather?lon=a&lat=0')
    assert_validation_error(response, {'lon': 'float_parsing'})


def test_get_current_weather_greater_coords(client):
    '''
    Запрос при выходе за допустимый диапазон значений обеих координат в 
    большую сторону -> 422 с ошибками по обоим полям.
    '''
    response = client.get('/current_weather?lat=91&lon=181')
    assert_validation_error(response, {'lon': 'less_than_equal', 'lat': 'less_than_equal'})


def test_get_current_weather_less_coords(client):
    '''
    Запрос при выходе за допустимый диапазон значений обеих координат в 
    меньшую сторону -> 422 с ошибками по обоим полям.
    '''
    response = client.get('/current_weather?lat=-91&lon=-181')
    assert_validation_error(response, {'lon': 'greater_than_equal', 'lat': 'greater_than_equal'})


def test_get_current_weather_timeout(client, mock_get_current):
    '''
    Таймаут при обращении Open Meteo API -> 504 ошибка.
    '''
    mock_get_current.side_effect = httpx.TimeoutException('Timeout')

    response = client.get('/current_weather?lat=0&lon=0')

    assert response.status_code == 504
    assert 'Open Meteo API did not respond in time' in response.json()['detail']


def test_get_current_weather_http_error(client, mock_get_current):
    '''
    Ошибка со стороны Open Meteo API на примере 503 (перегрузка сервера) -> 
    пробрасывается соответствующий статус.
    '''
    error_response = httpx.Response(503, json={'error': 'Service Unavailable'})
    mock_get_current.side_effect = httpx.HTTPStatusError(
        'Error', request=httpx.Request('GET', 'url'), response=error_response
    )

    response = client.get('/current_weather?lat=0&lon=0')

    assert response.status_code == 503
    assert 'Open Meteo API' in response.json()['detail']
