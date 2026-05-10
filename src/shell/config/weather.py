from util.secrets import WEATHER_API_KEY

WEATHER_API_URL = (
    "https://api.openweathermap.org/data/2.5/weather?zip=81647,"
    + f"us&units=imperial&appid={WEATHER_API_KEY}"
)
