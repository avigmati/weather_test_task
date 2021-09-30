import aiopg.sa
from sqlalchemy import (
    MetaData, Table, Column, ForeignKey, Integer, String, Date, Float, JSON, and_
)


meta = MetaData()

location = Table(
    'location', meta,

    Column('id', Integer, primary_key=True),
    Column('city', String(200), nullable=False),
    Column('country_code', String(2), nullable=False),
    Column('lat', Float(), nullable=False),
    Column('lon', Float(), nullable=False)
)


weather = Table(
    'weather', meta,

    Column('id', Integer, primary_key=True),
    Column('location_id', Integer, ForeignKey('location.id', ondelete='CASCADE')),
    Column('dt', Integer(), nullable=False),
    Column('data', JSON(), nullable=False)
)


async def pg_context(app):
    settings = app['settings'].DATABASE
    engine = await aiopg.sa.create_engine(
        database=settings['name'],
        user=settings['user'],
        password=settings['password'],
        host=settings['host'],
        port=settings['port'],
        minsize=settings['minsize'],
        maxsize=settings['maxsize']
    )
    app['db'] = engine

    yield

    app['db'].close()
    await app['db'].wait_closed()


async def get_location(engine, city, country_code):
    async with engine.acquire() as conn:
        cursor = await conn.execute(location.select().where(
                and_(
                    location.c.city == city,
                    location.c.country_code == country_code,
                )
            )
        )
        loc = await cursor.fetchone()
        return dict(loc) if loc else None


async def create_location(engine, data):
    async with engine.acquire() as conn:
        loc = await conn.execute(
            location.insert().values(**data).returning(location)
        )
        return await loc.fetchone()


async def create_weather(engine, data, location):
    async with engine.acquire() as conn:
        for w in data:
            _w = {'dt': w['dt'], 'data': w, 'location_id': location['id']}
            await conn.execute(
                weather.insert().values(**_w)
            )


async def get_weather(engine, dt, location):
    async with engine.acquire() as conn:
        cursor = await conn.execute(weather.select().where(
                and_(
                    weather.c.location_id == location['id'],
                    weather.c.dt == dt,
                )
            )
        )
        w = await cursor.fetchone()
        return dict(w) if w else None

