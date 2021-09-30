## Run via docker-compose
```shell
$ API_KEY="your openweathermap.org api key" docker-compose up
```

## Run native
 
1) create virtual environment
```shell
$ python3.9 -m venv .venv
```

2) activae it
```shell
$ source .venv/bin/activate
```

3) install dependencies
```shell
$ pip install requirements.txt
```

4) create postgres database

5) configure app via editing ```settings.py```

6) initialize db
```shell
$ python init_db.py
```

7) run app
```shell
$ python app.py
```

## Request format
```http://0.0.0.0:8000/?country_code=RU&city=Moscow&date=03.10.2021T12:11```