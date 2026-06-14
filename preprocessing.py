def clean_and_extract(weather_data):
    # Example preprocessing: ensure all keys are present and valid
    defaults = {"temperature": 25, "humidity": 50, "rainfall": 2, "soil_moisture": 50}
    clean_data = {k: weather_data.get(k, defaults[k]) for k in defaults}
    clean_data['ndvi_grid'] = weather_data.get('ndvi_grid', [[0.4]*10]*10)
    return clean_data
