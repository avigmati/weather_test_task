import aiopg.sa
from sqlalchemy import (
    MetaData, Table, Column, ForeignKey, Integer, String, Date, Float, and_
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
        record = await cursor.fetchone()
        return dict(record) if record else None


async def create_location(engine, data):
    async with engine.acquire() as conn:
        task = await conn.execute(
            location.insert().values(**data).returning(location)
        )
        return await task.fetchone()
