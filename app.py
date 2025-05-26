from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
AQI_API_TOKEN = os.getenv('AQI_API_KEY')

if not AQI_API_TOKEN:
    raise ValueError("Missing AQI API Key. Add it in .env file as AQI_API_KEY")

# Base API URL for AQI by city
AQI_API_URL = 'https://api.waqi.info/feed/{city}/?token=' + AQI_API_TOKEN

# AQI Breakpoints
AQI_BREAKPOINTS = {
    'pm25': [(0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
             (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 350.4, 301, 400), (350.5, 500.4, 401, 500)],
    'pm10': [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
             (255, 354, 151, 200), (355, 424, 201, 300), (425, 504, 301, 400), (505, 604, 401, 500)],
    'no2': [(0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
            (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 1649, 301, 400), (1650, 2049, 401, 500)],
    'so2': [(0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
            (186, 304, 151, 200), (305, 604, 201, 300), (605, 804, 301, 400), (805, 1004, 401, 500)],
    'co': [(0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
           (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 40.4, 301, 400), (40.5, 50.4, 401, 500)],
    'o3': [(0.0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150),
           (86, 105, 151, 200), (106, 200, 201, 300), (201, 300, 301, 400), (301, 400, 401, 500)]
}

# AQI Calculation Function
def calculate_individual_aqi(pollutant, concentration):
    breakpoints = AQI_BREAKPOINTS.get(pollutant)
    if not breakpoints:
        return None

    for bp_low, bp_high, aqi_low, aqi_high in breakpoints:
        if bp_low <= concentration <= bp_high:
            aqi = ((aqi_high - aqi_low) / (bp_high - bp_low)) * (concentration - bp_low) + aqi_low
            return round(aqi)
    return None

# ----------------- ROUTES ------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calculate-aqi', methods=['GET', 'POST'])
def calculate_aqi():
    aqi_results = {}
    max_aqi = None
    max_pollutant = None
    city = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city')
        try:
            response = requests.get(AQI_API_URL.format(city=city))
            data = response.json()

            if data['status'] == 'ok':
                iaqi_data = data['data']['iaqi']
                for pollutant in AQI_BREAKPOINTS.keys():
                    if pollutant in iaqi_data:
                        concentration = iaqi_data[pollutant].get('v')
                        aqi = calculate_individual_aqi(pollutant, concentration)
                        if aqi is not None:
                            aqi_results[pollutant] = aqi
                            if max_aqi is None or aqi > max_aqi:
                                max_aqi = aqi
                                max_pollutant = pollutant
            else:
                error = f"API error: {data.get('data', 'Unknown error')}"
        except Exception as e:
            error = f"Request failed: {str(e)}"

    return render_template(
        'calculate-aqi.html',
        city=city,
        aqi_results=aqi_results,
        max_aqi=max_aqi,
        max_pollutant=max_pollutant,
        error=error
    )

@app.route('/calculate-wqi', methods=['GET', 'POST'])
def calculate_wqi():
    wqi_value = None
    wqi_status = None
    location = None
    error = None

    if request.method == 'POST':
        location = request.form.get('location')
        try:
            # Simulated water data
            ph = 7.4
            do = 8.0
            bod = 2.0

            # WQI formula (example)
            wqi_value = round((ph * 0.2 + do * 0.5 - bod * 0.3) * 10, 2)

            if wqi_value >= 80:
                wqi_status = 'Excellent'
            elif wqi_value >= 60:
                wqi_status = 'Good'
            elif wqi_value >= 40:
                wqi_status = 'Poor'
            else:
                wqi_status = 'Very Poor'
        except Exception as e:
            error = f"Error calculating WQI: {str(e)}"

    return render_template(
        'calculate-wqi.html',
        wqi=wqi_value,
        status=wqi_status,
        location=location,
        error=error
    )

# ----------------- MAIN ------------------
if __name__ == '__main__':
    app.run(debug=True)
