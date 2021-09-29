from sqlalchemy import create_engine, MetaData

import settings
from db import location


def create_tables(engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[location, ])


if __name__ == '__main__':
    db_url = "postgresql://{user}:{password}@{host}:{port}/{name}".format(**settings.DATABASE)
    engine = create_engine(db_url)
    create_tables(engine)
