import os
from loguru import logger

# Open Weather Maps
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", default="")
if WEATHER_API_KEY == "":
    logger.warning(
        "API key needed for weather module not found. Export an environment variable"
        + " named WEATHER_API_KEY with your key for Open Weather Maps."
    )
