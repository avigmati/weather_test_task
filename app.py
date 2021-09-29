import aiohttp
from aiohttp import web
from pydantic import BaseModel, validator
from pydantic import ValidationError
from datetime import datetime
import json
import settings
import db


class GetLocationError(Exception):
    pass


class LocationNotFound(Exception):
    pass


class RequestValidator(BaseModel):
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


async def get_location(session, request, country_code, city):
    try:
        # pass
        location = await db.get_location(request.app['db'], city, country_code)
        if not location:
            r = f'http://api.openweathermap.org/geo/1.0/direct?q={city},{country_code}&limit={1}&appid={settings.API_KEY}'
            async with session.get(r) as response:
                data = json.loads(await response.text())
                if not data:
                    raise LocationNotFound(f'Requested location not found, city: {city}, country_code: {country_code}')
                lat, lon = data[0].get('lat'), data[0].get('lon')
                location = await db.create_location(request.app['db'],
                                                    {'city': city, 'country_code': country_code, 'lat': lat, 'lon': lon})
        return location
    except LocationNotFound as e:
        raise e
    except Exception as e:
        raise GetLocationError(e.__repr__())


async def handle(request):
    try:
        req = RequestValidator(**request.query)
        async with aiohttp.ClientSession() as session:
            location = await get_location(session, request, req.country_code, req.city)
        response = web.Response(text=json.dumps(location))

    except ValidationError as e:
        response = web.Response(text=json.dumps(e.errors()), status=400)
    except LocationNotFound as e:
        response = web.Response(text=json.dumps({'error': e.__str__()}), status=404)

    return response


app = web.Application()
app.add_routes([web.get('/', handle)])


if __name__ == '__main__':
    app['settings'] = settings
    app.cleanup_ctx.append(db.pg_context)
    web.run_app(app)
