import aiohttp
from aiohttp import web
from pydantic import BaseModel, validator
from pydantic import ValidationError
from datetime import datetime, timedelta
import json
import settings
import db


class GetLocationError(Exception):
    pass


class GetWeatherError(Exception):
    pass


class FetchError(Exception):
    def __init__(self, code, data=None):
        self.code = code
        self.data = data


class Request(BaseModel):
    country_code: str
    city: str
    date: str

    @validator('date')
    def validate_date(cls, value):
        if not isinstance(value, str):
            raise ValueError('date must be string')
        try:
            value = datetime.strptime(value, '%d.%m.%YT%H:%M')
        except Exception as e:
            raise ValueError('wrong date format')
        return value

    @validator('country_code')
    def validate_country_code(cls, value):
        if not isinstance(value, str):
            raise ValueError('country_code must be string')

        if not len(value) == 2:
            raise ValueError('country_code must be a string two characters long')

        return value.upper()

    @validator('city')
    def validate_city(cls, value):
        if not isinstance(value, str):
            raise ValueError('city must be string')

        if len(value) < 2:
            raise ValueError('must be a string at least two characters long')

        return value.capitalize()


async def fetch(session, url):
    async with session.get(url) as response:
        data = json.loads(await response.text())
        if not response.status == 200:
            raise FetchError(code=response.status, data=data)
        if not data:
            raise FetchError(code=404)
        return data


async def get_location(session, request, country_code, city):
    try:
        location = await db.get_location(request.app['db'], city, country_code)
        if not location:
            data = await fetch(session,
                f'http://api.openweathermap.org/geo/1.0/direct?q={city},{country_code}&limit={1}&appid={settings.API_KEY}'
            )
            lat, lon = data[0].get('lat'), data[0].get('lon')
            location = await db.create_location(request.app['db'],
                                                {'city': city, 'country_code': country_code, 'lat': lat, 'lon': lon})
        return location
    except FetchError as e:
        e.data = {'error': 'location not found'} if not e.data else e.data
        raise e
    except Exception as e:
        raise GetLocationError(e.__repr__())


async def get_weather(session, request, location, date):
    try:
        dt_req, dt_now = int(date.timestamp()), int(datetime.now().timestamp())
        # rounds to nearest hour by adding a timedelta hour if minute >= 30
        dt_rounded = int((date.replace(second=0, microsecond=0, minute=0, hour=date.hour) +
                          timedelta(hours=date.minute // 30)).timestamp())

        weather = await db.get_weather(request.app['db'], dt_rounded, location)
        weather = weather['data'] if weather else None

        if not weather:
            if dt_now > dt_req:
                # request historical data
                data = await fetch(session,
                                   f'https://api.openweathermap.org/data/2.5/onecall/timemachine?'
                                   f'lat={location["lat"]}&lon={location["lon"]}&dt={dt_req}&appid={settings.API_KEY}'
                                   )
            else:
                # request forecast data
                data = await fetch(session,
                                   f'https://api.openweathermap.org/data/2.5/onecall?'
                                   f'lat={location["lat"]}&lon={location["lon"]}&appid={settings.API_KEY}'
                                   )
            await db.create_weather(request.app['db'], data['hourly'], location)
            weather = data['current']
        return weather
    except FetchError as e:
        e.data = {'error': 'weather not found'} if not e.data else e.data
        raise e
    except Exception as e:
        raise GetWeatherError(e.__repr__())


async def handle(request):
    try:
        req = Request(**request.query)
        async with aiohttp.ClientSession() as session:
            location = await get_location(session, request, req.country_code, req.city)
            weather = await get_weather(session, request, location, req.date)
        response = web.Response(text=json.dumps(weather), content_type='application/json')

    except ValidationError as e:
        response = web.Response(text=json.dumps(e.errors()), status=400, content_type='application/json')
    except FetchError as e:
        response = web.Response(text=json.dumps(e.data), status=e.code, content_type='application/json')

    return response


app = web.Application()
app.add_routes([web.get('/', handle)])


if __name__ == '__main__':
    app['settings'] = settings
    app.cleanup_ctx.append(db.pg_context)
    web.run_app(app)
