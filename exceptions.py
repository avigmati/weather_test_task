class GetLocationError(Exception):
    pass


class GetWeatherError(Exception):
    pass


class FetchError(Exception):
    def __init__(self, code, data=None):
        self.code = code
        self.data = data
