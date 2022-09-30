import requests as r
from KEYS import AMBEE_KEY
from time import sleep
import datetime


class AmbeeData:
    def __init__(self):
        """
        A class for accessing and using the features of the AMBEE API
        - Currently the weather functionality is used, but others can be added to feature in the Fire Risk Assessment
        """
        self.headers = {"x-api-key": AMBEE_KEY, "Accept": "application/json"}

    def get_weather_lat_lon(self, lat, lon):
        """
        Gets the current weather data given the latitude and longitude coordinates
        - Currently the data provided includes temperature, humidity, wind_speed, precipitation (more can be added if wanted)
        :param lat: Latitude Coordinate
        :param lon: Longitude Coordinate
        :return: Dict of data (dict)
        """
        url = f'https://api.ambeedata.com/weather/latest/by-lat-lng?lat={lat}&lng={lon}'
        try:
            ambee_weather = r.get(url, headers=self.headers).json()
        except:
            sleep(1)
            ambee_weather = r.get(url, headers=self.headers).json()
        ambee_weather = ambee_weather['data']
        temp, humidity, wind_speed, precip = ambee_weather['apparentTemperature'], ambee_weather['humidity'], \
                                             ambee_weather['windSpeed'], ambee_weather['dewPoint']
        return {"temp": temp, "vapr": humidity, "wind": wind_speed, "prec": precip}

    def get_weather_history(self, lat, lon, start, end=None):
        """
        Gets the current weather data given the latitude and longitude coordinates
        - Currently the data provided includes temperature, humidity, wind_speed, precipitation (more can be added if wanted)
        :param lat: Latitude Coordinate
        :param lon: Longitude Coordinate
        :param start: Start date in format %Y-%m-%d (str)
        :param end: [OPTIONAL] end date in format %Y-%m-%d (str)
        :return: Dict of data (dict)
        """
        start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
        if not end:
            end_date = start_date + datetime.timedelta(days=1)
            end = end_date.strftime('%Y-%m-%d')
        start = start + " 00:00:00"
        end = end + " 00:00:00"
        try:
            url = f'https://api.ambeedata.com/weather/history/daily/by-lat-lng?lat={lat}&lng={lon}&from={start}&to={end}'
        except:
            sleep(1)
            url = f'https://api.ambeedata.com/weather/history/daily/by-lat-lng?lat={lat}&lng={lon}&from={start}&to={end}'

        ambee_weather_hist = r.get(url, headers=self.headers).json()
        ambee_weather_hist = ambee_weather_hist['data']['history'][0]
        temp, humidity, wind_speed, precip = ambee_weather_hist['apparentTemperature'], ambee_weather_hist['humidity'], \
                                             ambee_weather_hist['windSpeed'], ambee_weather_hist['dewPoint']

        return {"temp": temp, "vapr": humidity, "wind": wind_speed, "prec": precip}

    def get_soil_lat_lon(self, lat, lon):
        """
        Gets the soil data given the latitude and longitude coordinates
        :param lat: Latitude Coordinate
        :param lon: Longitude Coordinate
        :return: Dict of data (dict)
        """
        url = f'https://api.ambeedata.com/soil/latest/by-lat-lng?lat={lat}&lng={lon}'
        ambee_soil = r.get(url, headers=self.headers).json()
        return ambee_soil

    def get_current_ndvi(self, lat, lon):
        """
        Gets the ndvi data given the latitude and longitude coordinates
        :param lat: Latitude Coordinate
        :param lon: Longitude Coordinate
        :return: Dict of data (dict)
        """
        url = f'https://api.ambeedata.com/ndvi/latest/by-lat-lng?lat={lat}&lng={lon}'
        ambee_ndvi = r.get(url, headers=self.headers).json()
        return ambee_ndvi

    def get_current_watervapor(self, lat, lon):
        """
        Gets the water vapor data given the latitude and longitude coordinates
        :param lat: Latitude Coordinate
        :param lon: Longitude Coordinate
        :return: Dict of data (dict)
        """
        url = f'https://api.ambeedata.com/waterVapor/latest/by-lat-lng?lat={lat}&lng={lon}'
        ambee_wv = r.get(url, headers=self.headers).json()
        return ambee_wv
