from flask import Flask, render_template, request, jsonify
from data_ingest import get_weather
from crop_model import twin
from predictor import predict_soil_moisture, generate_recommendations
from preprocessing import clean_and_extract
import pandas as pd
import datetime
import json
import random
import os

app = Flask(__name__)

# ---------------------------
# Simple in-memory cache
# ---------------------------
_cached = {
    'forecast': None,
    'weather': None,
    'timestamp': None,
}

# ---------------------------
# Simulated historical soil moisture history
# ---------------------------
history_df = pd.DataFrame({
    'ds': pd.date_range(datetime.date.today() - pd.Timedelta(days=30), periods=30),
    'y': [random.uniform(25, 65) for _ in range(30)]
})

# ---------------------------
# Weather summary helper
# ---------------------------
def weather_recommendation(weather):
    rain = weather.get('rainfall', 0)
    humidity = weather.get('humidity', 0)
    temperature = weather.get('temperature', 0)

    if rain > 2:
        return "Rain is expected, which should help with irrigation."
    elif humidity < 30:
        return "Humidity is low, so avoid overwatering and watch for plant stress."
    elif temperature > 30:
        return "It will be quite hot, so keep an eye on soil moisture."
    else:
        return "Weather looks stable and suitable for crop growth."

# ---------------------------
# Turn model recs into farmer-friendly one-liners
# ---------------------------
def humanize_recommendation(rec):
    day = rec.get('day')
    soil = rec.get('pred_soil')
    action = rec.get('action')

    if soil is None:
        soil_text = "soil moisture is not available"
    else:
        soil_text = f"moisture about {soil:.1f}%"

    if action == "irrigate":
        templates = [
            "Day {day}: {soil_text}. Give the field some water.",
            "Day {day}: {soil_text}. Plan to irrigate.",
            "Day {day}: {soil_text}. Water the crop."
        ]
    elif action == "fertilize":
        templates = [
            "Day {day}: {soil_text}. Apply some fertilizer to support growth.",
            "Day {day}: {soil_text}. A light fertilizer dose is a good idea.",
            "Day {day}: {soil_text}. Add fertilizer to help the plants."
        ]
    else:  # wait / monitor
        templates = [
            "Day {day}: {soil_text}. Leave the field as it is and keep an eye on it.",
            "Day {day}: {soil_text}. No work needed, just watch the field.",
            "Day {day}: {soil_text}. You can wait and simply monitor."
        ]
    return random.choice(templates).format(day=day, soil_text=soil_text)

# ---------------------------
# MAIN DASHBOARD
# ---------------------------
@app.route('/')
def index():
    refresh = request.args.get('refresh', '0') == '1'

    # Get and clean weather data
    weather_raw = get_weather()
    weather = clean_and_extract(weather_raw)

    # Update the digital twin state
    twin.update(weather)

    # Load or regenerate forecast
    global _cached
    if _cached['forecast'] is None or refresh:
        forecast_df = predict_soil_moisture(history_df)
        _cached['forecast'] = forecast_df
        _cached['weather'] = weather
        _cached['timestamp'] = datetime.datetime.now().isoformat()
    else:
        forecast_df = _cached['forecast']
        _cached['weather'] = weather  # keep latest weather

    # Generate RL recommendations
    raw_recommendations, rec_explanation = generate_recommendations(
        forecast_df, recent_weather=weather
    )
    human_recommendations = [
        humanize_recommendation(r) for r in raw_recommendations
    ]

    weather_summary = weather_recommendation(weather)
    ndvi_json = json.dumps(weather.get('ndvi_grid', []))

    # Build farm_data grid for 3D rendering; for single plant twin this is 1x1
    farm_data = [[
        {
            "height": twin.height,
            "health": twin.health,
            "stage": twin.stage
        }
    ]]

    crop = {
        "height": twin.height,
        "health": twin.health,
        "stage": twin.stage,
        "rows": 1,
        "cols": 1,
        "stages": [[twin.stage]],
    }

    return render_template(
        'dashboard.html',
        crop=crop,
        farm_data=json.dumps(farm_data),
        weather=weather,
        forecast=forecast_df.to_dict(orient='records'),
        recommendations=human_recommendations,
        recommendations_text=rec_explanation,
        weather_recommendation=weather_summary,
        ndvi_json=ndvi_json
    )

# ---------------------------
# Force-refresh endpoint
# ---------------------------
@app.route('/refresh', methods=['POST'])
def refresh():
    global _cached
    forecast_df = predict_soil_moisture(history_df)
    weather_raw = get_weather()
    weather = clean_and_extract(weather_raw)

    generate_recommendations(forecast_df, recent_weather=weather)

    _cached['forecast'] = forecast_df
    _cached['weather'] = weather
    _cached['timestamp'] = datetime.datetime.now().isoformat()
    return jsonify({'status': 'ok', 'timestamp': _cached['timestamp']})

# ---------------------------
# Control actions (buttons)
# ---------------------------
@app.route('/control', methods=['POST'])
def control():
    action = request.json.get('action')
    twin.process_action(action)
    return jsonify({
        "stage": twin.stage,
        "height": twin.height,
        "health": twin.health
    })

# ---------------------------
# Admin page (Q-values + logs)
# ---------------------------
@app.route('/admin')
def admin():
    qvals = {}
    logs = {}

    try:
        import pickle
        p = os.path.join(os.path.dirname(__file__), 'q_agent.pkl')
        with open(p, 'rb') as f:
            agent = pickle.load(f)
        qvals = {str(k): agent.q[k] for k in agent.q}
    except Exception as e:
        qvals = {'error': str(e)}

    try:
        lpath = os.path.join(os.path.dirname(__file__), 'agent_logs.json')
        with open(lpath, 'r') as f:
            logs = json.load(f)
    except Exception as e:
        logs = {'error': str(e)}

    return render_template('admin.html', q_vals=qvals, logs=logs)

# ---------------------------
# Run app
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
