import requests
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

API_TOKEN = "1695ea87b2bd6ed0f4d84b096487ac6248887489" # Your confirmed API Token

@app.route('/')
def home():
    # Make sure your index.html is in a 'templates' folder relative to app.py
    return render_template('index.html')

@app.route('/search_city')
def search_city():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"status": "error", "data": "Missing search keyword"}), 400

    search_url = f"https://api.waqi.info/search/?token={API_TOKEN}&keyword={keyword}"
    print(f"DEBUG: Calling WAQI API for city search: {search_url}")

    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status() # Raises HTTPError for 4xx/5xx responses
        data = response.json()

        print(f"DEBUG: WAQI API Search Raw Response: {data}")

        if data.get('status') == 'ok':
            # Extract relevant info: station name, uid (ID), lat, lon
            results = []
            for item in data.get('data', []):
                # Ensure station and geo data exist before accessing
                station_name = item.get('station', {}).get('name')
                geo = item.get('station', {}).get('geo', [])
                
                # Only add if name and at least one coordinate are present
                if station_name and len(geo) == 2:
                    results.append({
                        'uid': item.get('uid'),
                        'name': station_name,
                        'lat': geo[0],
                        'lon': geo[1]
                    })
            return jsonify({"status": "ok", "data": results})
        else:
            return jsonify({"status": "error", "data": f"WAQI API search error: {data.get('data')}"}), 502
    except requests.exceptions.ConnectionError:
        return jsonify({"status": "error", "data": "Cannot connect to WAQI API for search."}), 503
    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "data": "WAQI API search request timed out."}), 504
    except requests.exceptions.HTTPError as e:
        return jsonify({"status": "error", "data": f"HTTP error during search: {str(e)}"}), response.status_code
    except Exception as e:
        return jsonify({"status": "error", "data": f"Unexpected error during city search: {str(e)}"}), 500


@app.route('/get_aqi') # This route now handles both geo and station_id
def get_aqi():
    user_lat = request.args.get('lat')
    user_lon = request.args.get('lon')
    station_id = request.args.get('station_id')

    url = ""
    is_geo_query = False # Flag to know if it's a geo query (for fallback logic)

    if station_id:
        url = f"https://api.waqi.info/feed/@{station_id}/?token={API_TOKEN}"
        print(f"DEBUG: Calling WAQI API for station ID: {url}")
    elif user_lat and user_lon:
        try:
            float(user_lat)
            float(user_lon)
        except ValueError:
            return jsonify({"status": "error", "data": "Invalid lat/lon format"}), 400
        url = f"https://api.waqi.info/feed/geo:{user_lat};{user_lon}/?token={API_TOKEN}"
        is_geo_query = True
        print(f"DEBUG: Calling WAQI API URL for geo location: {url}")
    else:
        return jsonify({"status": "error", "data": "Missing coordinates or station ID"}), 400

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        print(f"DEBUG: WAQI API Raw Response: {data}")

        if data.get('status') == 'ok':
            return jsonify(data)
        elif is_geo_query and data.get('status') == 'nope' and data.get('data') == 'can not connect':
            print(f"DEBUG: WAQI API returned: 'can not connect' for geo query. Attempting fallback to Kathmandu.")
            # --- Fallback to Kathmandu if initial geo attempt failed ---
            fallback_lat = "27.7172"
            fallback_lon = "85.3240"
            fallback_city_name = "Kathmandu"

            fallback_url = f"https://api.waqi.info/feed/geo:{fallback_lat};{fallback_lon}/?token={API_TOKEN}"
            print(f"DEBUG: Attempting fallback to {fallback_city_name}: {fallback_url}")

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
        else:
            # For other 'error' or 'nope' statuses not specifically 'can not connect' or 'Unknown station'
            return jsonify({"status": "error", "data": f"WAQI API error: {data.get('data')}"}), 502

    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to air quality API."
        if is_geo_query: # Only try fallback for geo queries if primary geo query failed due to connection
            print(f"DEBUG: ConnectionError during geo query. Attempting fallback.")
            fallback_lat = "27.7172"
            fallback_lon = "85.3240"
            fallback_city_name = "Kathmandu"

            fallback_url = f"https://api.waqi.info/feed/geo:{fallback_lat};{fallback_lon}/?token={API_TOKEN}"
            print(f"DEBUG: Attempting fallback to {fallback_city_name}: {fallback_url}")
            try:
                fallback_response = requests.get(fallback_url, timeout=10)
                fallback_response.raise_for_status()
                fallback_data = fallback_response.json()
                if fallback_data.get('status') == 'ok':
                    fallback_data['isFallback'] = True
                    fallback_data['fallbackCityName'] = fallback_city_name
                    return jsonify(fallback_data)
                else:
                    error_msg = f"Could not get air quality for your location. Fallback to {fallback_city_name} also failed: {fallback_data.get('data')} (Connection Error)."
            except Exception as fe: # Catch all errors from fallback attempt
                 error_msg = f"Could not connect to air quality API for your location or {fallback_city_name}: {str(fe)}."
        return jsonify({"status": "error", "data": error_msg}), 503

    except requests.exceptions.Timeout:
        error_msg = "Air quality API request timed out."
        if is_geo_query: # Only try fallback for geo queries if primary geo query failed due to timeout
            print(f"DEBUG: Timeout during geo query. Attempting fallback.")
            fallback_lat = "27.7172"
            fallback_lon = "85.3240"
            fallback_city_name = "Kathmandu"

            fallback_url = f"https://api.waqi.info/feed/geo:{fallback_lat};{fallback_lon}/?token={API_TOKEN}"
            print(f"DEBUG: Attempting fallback to {fallback_city_name}: {fallback_url}")
            try:
                fallback_response = requests.get(fallback_url, timeout=10)
                fallback_response.raise_for_status()
                fallback_data = fallback_response.json()
                if fallback_data.get('status') == 'ok':
                    fallback_data['isFallback'] = True
                    fallback_data['fallbackCityName'] = fallback_city_name
                    return jsonify(fallback_data)
                else:
                    error_msg = f"Could not get air quality for your location. Fallback to {fallback_city_name} also failed: {fallback_data.get('data')} (Timeout Error)."
            except Exception as fe:
                error_msg = f"Air quality API request timed out for your location or {fallback_city_name}: {str(fe)}."
        return jsonify({"status": "error", "data": error_msg}), 504

    except requests.exceptions.HTTPError as e:
        return jsonify({"status": "error", "data": f"HTTP error from API: {str(e)}"}), response.status_code

    except Exception as e:
        return jsonify({"status": "error", "data": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)