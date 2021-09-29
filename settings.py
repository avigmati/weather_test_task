import os

API_KEY = 'fc8535651fde9e9837312cff5b33a624'

DATABASE = {
    'name': 'weather',
    'user': 'postgres',
    'password': 'postgres',
    'host': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
    'port': '5432',
    'minsize': 1,
    'maxsize': 5
}
