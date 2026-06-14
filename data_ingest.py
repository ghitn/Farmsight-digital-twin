import random

_soil_moisture_cache = None

def get_soil_moisture():
    global _soil_moisture_cache
    if _soil_moisture_cache is None:
        import random
        _soil_moisture_cache = round(random.uniform(30, 70), 2)
    return _soil_moisture_cache


def get_ndvi_array(size=10):
    # Mock NDVI grid values from 0 to 1
    return [[round(random.uniform(0.1, 0.8), 2) for _ in range(size)] for _ in range(size)]

def get_weather():
    # Mock weather data for now
    return {
        "temperature": round(random.uniform(15, 35), 1),
        "humidity": round(random.uniform(30, 90), 1),
        "rainfall": round(random.uniform(0, 10), 1),
        "soil_moisture": get_soil_moisture(),
        "ndvi_grid": get_ndvi_array()
    }
