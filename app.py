import requests
import mysql.connector
from flask import Flask, render_template, jsonify, request, session, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
CORS(app, supports_credentials=True) # Enable CORS for credentials (cookies/sessions)

# --- Flask Session Configuration ---
# IMPORTANT: You MUST change this to a strong, random secret key for production.
# For a hackathon, os.urandom(24) is acceptable, but for deployment, use a hardcoded,
# complex string (e.g., 'your_super_secret_random_string_here_make_it_long_and_complex')
app.secret_key = os.urandom(24) # Generates a random 24-byte key
app.config['SESSION_TYPE'] = 'filesystem' # Stores sessions on the file system
app.config['SESSION_PERMANENT'] = False # Session expires when browser closes
app.config['SESSION_USE_SIGNER'] = True # Protects session cookie from tampering

# Ensure session is initialized
from flask_session import Session
Session(app)

# --- WAQI API Token ---
API_TOKEN = "1695ea87b2bd6ed0f4d84b096487ac6248887489" # Your confirmed WAQI API Token

# --- MySQL Database Configuration ---
# IMPORTANT: UPDATE THESE VALUES to match your XAMPP MySQL setup.
# You can find these in your phpMyAdmin or MySQL server configuration.
# The 'password' field is the MOST LIKELY culprit for 'Access denied' errors.
db_config = {
    'host': 'localhost', # Usually 'localhost' or '127.0.0.1' for XAMPP
    'user': 'root',      # Your MySQL username (default for XAMPP is often 'root')
    'password': '',      # <--- CRITICAL: Set this to your actual MySQL root password.
                         # If no password is set, leave it as an empty string ''.
                         # If you set a password (e.g., 'mypass'), change it to 'mypass'.
    'database': 'aircare' # <--- CORRECTED: Changed database name to 'aircare'
}

def get_db_connection():
    """Establishes and returns a new MySQL database connection."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

@app.route('/')
def home():
    """Renders the main HTML page of the application."""
    return render_template('index.html')

# --- User Authentication Routes ---
@app.route('/signup_user', methods=['POST'])
def signup_user():
    """Handles new user registration using username and password."""
    data = request.get_json()
    username = data.get('username') # Changed from email to username
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Check if username already exists in 'user_info' table
        cursor.execute("SELECT User_Name FROM user_info WHERE User_Name = %s", (username,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "User with this username already exists"}), 409

        # Hash password before storing
        password_hash = generate_password_hash(password)
        
        # Insert new user into 'user_info' table. Assuming User_id is AUTO_INCREMENT.
        # User_Name is set to the provided username.
        insert_query = """
        INSERT INTO user_info (User_Name, password_hash, User_Age, User_Location, User_Disease, disease_category)
        VALUES (%s, %s, 0, '', 'none', 'normal')
        """
        cursor.execute(insert_query, (username, password_hash))
        conn.commit()

        # Get the ID of the newly inserted user
        user_id = cursor.lastrowid 
        if not user_id: 
            cursor.execute("SELECT User_id FROM user_info WHERE User_Name = %s", (username,))
            user_id_row = cursor.fetchone()
            if user_id_row:
                user_id = user_id_row[0]
            else:
                raise Exception("Could not retrieve User_id after signup.")

        session['user_id'] = user_id # Log in the user by storing their ID in the session
        return jsonify({"status": "success", "message": "User registered successfully", "user_id": user_id}), 201

    except mysql.connector.Error as err:
        conn.rollback() 
        print(f"MySQL Error during signup: {err}")
        return jsonify({"status": "error", "message": f"Database error during signup: {err}"}), 500
    except Exception as e:
        conn.rollback()
        print(f"General Error during signup: {e}")
        return jsonify({"status": "error", "message": f'An unexpected error occurred during signup: {repr(e)}'}), 500
    finally:
        cursor.close()
        conn.close() 

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'aircarelogo.jpeg', mimetype='image/jpeg')

@app.route('/login_user', methods=['POST'])
def login_user():
    """Handles user login using username and password."""
    data = request.get_json()
    username = data.get('username') # Changed from email to username
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True) # Return rows as dictionaries for easy access
    try:
        # Fetch user by username from 'user_info' table
        cursor.execute("SELECT User_id, User_Name, password_hash FROM user_info WHERE User_Name = %s", (username,))
        user = cursor.fetchone()

        # Verify password
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['User_id'] # Store user ID in session upon successful login
            return jsonify({"status": "success", "message": "Login successful", "user_id": user['User_id']}), 200
        else:
            return jsonify({"status": "error", "message": "Invalid username or password"}), 401

    except mysql.connector.Error as err:
        print(f"MySQL Error during login: {err}")
        return jsonify({"status": "error", "message": f"Database error during login: {err}"}), 500
    except Exception as e:
        print(f"General Error during login: {e}")
        return jsonify({"status": "error", "message": f'An unexpected error occurred during login: {repr(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/logout_user', methods=['POST'])
def logout_user():
    """Handles user logout."""
    session.pop('user_id', None) # Remove user_id from session
    return jsonify({"status": "success", "message": "Logged out successfully"}), 200

@app.route('/get_current_user_id', methods=['GET'])
def get_current_user_id():
    """Returns the user_id from the current session, if logged in.
    Used by frontend to validate session on page load."""
    user_id = session.get('user_id')
    if user_id:
        return jsonify({"status": "ok", "user_id": user_id}), 200
    else:
        return jsonify({"status": "error", "message": "No user logged in"}), 401

# --- NEW: User Profile Retrieval Route ---
@app.route('/get_profile', methods=['GET'])
def get_profile():
    """
    Fetches the profile data for the currently logged-in user.
    """
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized: No user logged in"}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True) # Return rows as dictionaries
    try:
        cursor.execute(
            "SELECT User_Name, User_Age, User_Location, User_Disease, disease_category FROM user_info WHERE User_id = %s",
            (user_id,)
        )
        profile_data = cursor.fetchone()

        if profile_data:
            return jsonify({"status": "ok", "profile": profile_data}), 200
        else:
            return jsonify({"status": "error", "message": "Profile not found for this user."}), 404
    except mysql.connector.Error as err:
        print(f"MySQL Error during profile fetch: {err}")
        return jsonify({"status": "error", "message": f"Database error during profile fetch: {err}"}), 500
    except Exception as e:
        print(f"General Error during profile fetch: {e}")
        return jsonify({"status": "error", "message": f'An unexpected error occurred during profile fetch: {repr(e)}'}), 500
    finally:
        cursor.close()
        conn.close()


# --- User Profile Management Routes ---
@app.route('/save_profile', methods=['POST'])
def save_profile():
    """Saves or updates user profile data."""
    # Ensure user is logged in
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized: No user logged in"}), 401

    user_id = session['user_id'] # Get user ID from session
    data = request.get_json()
    user_name = data.get('name', '') # 'name' from frontend maps to User_Name in DB
    user_age = data.get('age')
    user_location = data.get('location', '')
    user_disease = data.get('disease', 'none')
    disease_category = data.get('diseaseCategory', 'normal')

    conn = get_db_connection()
    if conn is None:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Update user's profile in the 'user_info' table using correct column names
        update_query = """
        UPDATE user_info
        SET User_Name = %s, User_Age = %s, User_Location = %s, User_Disease = %s, disease_category = %s
        WHERE User_id = %s
        """
        cursor.execute(update_query, (user_name, user_age, user_location, user_disease, disease_category, user_id))
        conn.commit() 
        return jsonify({"status": "success", "message": "Profile saved successfully"}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"MySQL Error during profile save: {err}")
        return jsonify({"status": "error", "message": f"Database error during profile save: {err}"}), 500
    except Exception as e:
        conn.rollback()
        print(f"General Error during profile save: {e}")
        return jsonify({"status": "error", "message": f'An unexpected error occurred during profile save: {repr(e)}'}), 500
    finally:
        cursor.close()
        conn.close()

# --- WAQI API Proxy Routes (Unchanged from previous versions) ---
# These routes act as a proxy to the World Air Quality Index API.
# They are separate from the user authentication/profile management.
@app.route('/search_city')
def search_city_waqi(): 
    """
    Searches for air quality stations based on a keyword using the WAQI API.
    Returns a list of matching stations with their UID, name, latitude, and longitude.
    """
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"status": "error", "data": "Missing search keyword"}), 400

    search_url = f"https://api.waqi.info/search/?token={API_TOKEN}&keyword={keyword}"
    print(f"DEBUG: Calling WAQI API for city search: {search_url}")

    try:
        response = requests.get(search_url, timeout=10)
        response.raise_for_status() 
        data = response.json()

        print(f"DEBUG: WAQI API Search Raw Response: {data}")

        if data.get('status') == 'ok':
            results = []
            for item in data.get('data', []):
                station_name = item.get('station', {}).get('name')
                geo = item.get('station', {}).get('geo', [])
                
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
        return jsonify({"status": "error", "data": f'Unexpected error during city search: {repr(e)}'}), 500


@app.route('/get_aqi')
def get_aqi_waqi(): 
    """
    Fetches current air quality data either by latitude/longitude or by station ID.
    Includes a fallback to Kathmandu if geo-location query fails.
    """
    user_lat = request.args.get('lat')
    user_lon = request.args.get('lon')
    station_id = request.args.get('station_id')

    url = ""
    is_geo_query = False 

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
            return jsonify({"status": "error", "data": f"WAQI API error: {data.get('data')}"}), 502

    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to air quality API."
        if is_geo_query: 
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
            except Exception as fe: 
                 error_msg = f"Could not connect to air quality API for your location or {fallback_city_name}: {str(fe)}."
        return jsonify({"status": "error", "data": error_msg}), 503

    except requests.exceptions.Timeout:
        error_msg = "Air quality API request timed out."
        if is_geo_query: 
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
        return jsonify({"status": "error", "data": f'Unexpected error: {repr(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
