import requests
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_TOKEN = "1695ea87b2bd6ed0f4d84b096487ac6248887489" # Your confirmed API Token

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_aqi')
def get_aqi():
    user_lat = request.args.get('lat')
    user_lon = request.args.get('lon')

    if not user_lat or not user_lon:
        return jsonify({"status": "error", "data": "Missing or invalid coordinates"}), 400

    try:
        float(user_lat)
        float(user_lon)
    except ValueError:
        return jsonify({"status": "error", "data": "Invalid lat/lon format"}), 400

    # --- Attempt to get data for user's exact location ---
    initial_url = f"https://api.waqi.info/feed/geo:{user_lat};{user_lon}/?token={API_TOKEN}"
    print(f"DEBUG: Calling WAQI API URL for user's location: {initial_url}")

    try:
        initial_response = requests.get(initial_url, timeout=10)
        initial_response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
        initial_data = initial_response.json()

        print(f"DEBUG: WAQI API Raw Response for user's location: {initial_data}")

        if initial_data.get('status') == 'ok':
            # If successful, return the data for the user's location
            return jsonify(initial_data)
        elif initial_data.get('status') == 'error' and initial_data.get('data') == 'Unknown station':
            print(f"DEBUG: WAQI API returned: {initial_data.get('data')}. Attempting fallback.")
        elif initial_data.get('status') == 'nope' and initial_data.get('data') == 'can not connect':
            print(f"DEBUG: WAQI API returned: 'can not connect'. Attempting fallback.")
        else:
            print(f"DEBUG: WAQI API returned status '{initial_data.get('status')}' with data: {initial_data.get('data')}. Attempting fallback.")

    except requests.exceptions.ConnectionError:
        print("DEBUG: ConnectionError to WAQI API for user's location.")
    except requests.exceptions.Timeout:
        print("DEBUG: Timeout connecting to WAQI API for user's location.")
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: HTTPError from WAQI API for user's location: {str(e)}. Attempting fallback.")
    except Exception as e:
        print(f"DEBUG: Unexpected error during initial WAQI API call: {str(e)}. Attempting fallback.")

    # --- Fallback to Kathmandu if initial attempt failed or returned specific errors ---
    fallback_lat = "27.7172"
    fallback_lon = "85.3240"
    fallback_city_name = "Kathmandu"

    fallback_url = f"https://api.waqi.info/feed/geo:{fallback_lat};{fallback_lon}/?token={API_TOKEN}"
    print(f"DEBUG: Attempting fallback to {fallback_city_name}: {fallback_url}")

    try:
        fallback_response = requests.get(fallback_url, timeout=10)
        fallback_response.raise_for_status()
        fallback_data = fallback_response.json()

        print(f"DEBUG: WAQI API Raw Response for fallback: {fallback_data}")

        if fallback_data.get('status') == 'ok':
            fallback_data['isFallback'] = True
            fallback_data['fallbackCityName'] = fallback_city_name
            return jsonify(fallback_data)
        else:
            print(f"DEBUG: Fallback to {fallback_city_name} also failed: {fallback_data.get('data')}")
            return jsonify({"status": "error", "data": f"Could not get air quality for your location. Fallback to {fallback_city_name} also failed: {fallback_data.get('data')}"}), 502

    except requests.exceptions.ConnectionError:
        print(f"DEBUG: ConnectionError to WAQI API for {fallback_city_name}.")
        return jsonify({"status": "error", "data": f"Could not connect to air quality API for your location or {fallback_city_name}."}), 503
    except requests.exceptions.Timeout:
        print(f"DEBUG: Timeout connecting to WAQI API for {fallback_city_name}.")
        return jsonify({"status": "error", "data": f"Air quality API request timed out for your location or {fallback_city_name}."}), 504
    except requests.exceptions.HTTPError as e:
        print(f"DEBUG: HTTPError from WAQI API for {fallback_city_name}: {str(e)}.")
        return jsonify({"status": "error", "data": f"HTTP error from API for your location or {fallback_city_name}: {str(e)}"}), fallback_response.status_code
    except Exception as e:
        print(f"DEBUG: Unexpected error during fallback WAQI API call: {str(e)}.")
        return jsonify({"status": "error", "data": f"Unexpected error while getting air quality: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)