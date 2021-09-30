import os

API_KEY = os.environ.get('API_KEY', 'fake')

DATABASE = {
    'name': os.environ.get('POSTGRES_DB', 'weather'),
    'user': os.environ.get('POSTGRES_USER', 'postgres'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
    'host': os.environ.get('POSTGRES_HOST', '127.0.0.1'),
    'port': '5432',
    'minsize': 1,
    'maxsize': 5
}
