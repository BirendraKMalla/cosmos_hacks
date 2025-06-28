# cosmos_hacks
Air Quality Health Companion
1. Project Overview
The Air Quality Health Companion is a web application designed to empower users with real-time air quality information and personalized health advisories. It aims to help individuals, especially those with pre-existing health conditions, make informed decisions about their outdoor activities based on local air quality levels.

The application features a user authentication system, allowing for personalized profiles where users can specify their health conditions. It integrates with the World Air Quality Index (WAQI) API to fetch live AQI data for various locations, presenting it on an interactive map.

2. Key Features
User Authentication: Secure signup and login system using username and password.

Personalized User Profiles: Users can save their name, age, primary location, and select from a list of health conditions (e.g., allergies, asthma, heart disease).

Dynamic Health Advisories: Based on the user's saved health profile and the current AQI level, the application provides tailored health recommendations.

Interactive Air Quality Map: Utilizes Leaflet.js to display a map where users can click to get AQI data for specific coordinates.

City Search for AQI: Allows users to search for air quality stations by city name and view their AQI data.

Real-time AQI Data: Integrates with the WAQI API to fetch up-to-date air quality index and pollutant data (PM2.5, PM10).

Fallback Location: If real-time geo-location data is unavailable, the application defaults to showing air quality for Kathmandu.

Responsive Design: Built with Tailwind CSS for a modern and adaptive user interface across different devices.

3. Technologies Used
Backend (Flask - app.py)
Python 3: The core programming language.

Flask: A lightweight web framework for building the API and serving HTML.

mysql.connector: Python driver for interacting with MySQL database.

werkzeug.security: For secure password hashing (generate_password_hash, check_password_hash).

requests: For making HTTP requests to external APIs (WAQI API).

flask_cors: To handle Cross-Origin Resource Sharing, allowing frontend and backend to communicate.

flask_session: For managing server-side sessions to maintain user login state.

MySQL: The relational database used to store user information.

Frontend (index.html)
HTML5: Structure of the web application.

CSS3 (Tailwind CSS): For styling and responsive design. Tailwind CSS is used via CDN for rapid prototyping.

JavaScript (Vanilla JS): Client-side logic for user interaction, API calls, and dynamic content updates.

Leaflet.js: An open-source JavaScript library for interactive maps.

External APIs:

World Air Quality Index (WAQI) API: Provides real-time air quality data.

4. Setup Instructions
To get the Air Quality Health Companion running on your local machine, follow these steps:

4.1. Prerequisites
Python 3.x: Make sure Python is installed.

XAMPP (or equivalent LAMP/MAMP stack): This provides Apache (web server) and MySQL (database). Ensure MySQL is running.

Internet Connection: Required to fetch data from the WAQI API.

4.2. Database Setup (MySQL)
Start MySQL: Ensure your MySQL server (via XAMPP Control Panel) is running.

Access phpMyAdmin: Open your web browser and go to http://localhost/phpmyadmin.

Create Database and Table:

Go to the "SQL" tab.

Paste and execute the following SQL commands to create the aircare database and the user_info table:

-- Create the database named 'aircare'
CREATE DATABASE IF NOT EXISTS aircare;

-- Select the 'aircare' database
USE aircare;

-- Create the 'user_info' table
CREATE TABLE IF NOT EXISTS user_info (
    User_id INT AUTO_INCREMENT PRIMARY KEY,
    User_Name VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    User_Age INT DEFAULT 0,
    User_Location VARCHAR(255) DEFAULT '',
    User_Disease VARCHAR(255) DEFAULT 'none',
    disease_category VARCHAR(255) DEFAULT 'normal'
);

Configure app.py Database Credentials:

Open your app.py file.

Locate the db_config dictionary and ensure the user and password match your MySQL root credentials. By default, XAMPP's root user often has an empty password.

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # <--- IMPORTANT: Set your actual MySQL root password here
    'database': 'aircare'
}

4.3. Backend Setup (Flask)
Create Project Directory: Create a folder for your project (e.g., air_quality_app).

Place app.py and index.html: Put your app.py and index.html files directly inside this folder.

Create static Folder: Inside your project directory, create a new folder named static.

Place Favicon: Put your aircarelogo.jpeg file inside the static folder.
(Example structure: air_quality_app/static/aircarelogo.jpeg)

Install Python Dependencies:

Open your terminal or command prompt.

Navigate to your project directory: cd path/to/your/air_quality_app

Install the required Python packages:

pip install Flask Flask-Cors Flask-Session mysql-connector-python requests werkzeug

Run the Flask Application:

python app.py

You should see output indicating the Flask server is running, typically on http://127.0.0.1:5000.

4.4. Frontend Access (index.html)
Open in Browser: Open your web browser and navigate to http://127.0.0.1:5000.

Clear Browser Cache (Important for Favicon): If the favicon doesn't appear immediately, clear your browser's cache (especially for images/favicons) and refresh the page.

5. Database Schema
The user_info table stores the following user data:

Column Name

Data Type

Constraints

Description

User_id

INT

PRIMARY KEY, AUTO_INCREMENT

Unique identifier for each user.

User_Name

VARCHAR(255)

UNIQUE, NOT NULL

User's chosen username for login.

password_hash

VARCHAR(255)

NOT NULL

Hashed password for security.

User_Age

INT

DEFAULT 0

User's age. Defaults to 0 if not provided.

User_Location

VARCHAR(255)

DEFAULT ''

User's primary city/region.

User_Disease

VARCHAR(255)

DEFAULT 'none'

User's selected health condition.

disease_category

VARCHAR(255)

DEFAULT 'normal'

Categorized health risk (normal, high, critical).

6. API Integration
The application integrates with the World Air Quality Index (WAQI) API (https://aqicn.org/api/).

API Token: Your API token (1695ea87b2bd6ed0f4d84b096487ac6248887489) is configured in app.py.

Endpoints Used:

/search/?token={token}&keyword={keyword}: For searching cities/stations.

/feed/geo:{lat};{lon}/?token={token}: For fetching AQI by geographical coordinates.

/feed/@{station_id}/?token={token}: For fetching AQI by station ID.

7. Future Enhancements
User Location Auto-detection: Implement browser's geolocation API to automatically detect user's current location for AQI.

Historical Data & Trends: Display historical AQI data and trends for selected locations.

Push Notifications/Alerts: Implement a system for sending real-time air quality alerts to users (e.g., via email or a simple in-app notification system).

More Granular Health Conditions: Expand the list of health conditions and provide more specific advisories.

Interactive Pollutant Details: Allow users to click on individual pollutants (PM2.5, PM10, O3, NO2, SO2, CO) to see their health effects.

User Feedback/Reporting: Allow users to report local air quality observations.

Improved UI/UX: Further refine the user interface with more animations, transitions, and accessibility features.

Dockerization: Containerize the application using Docker for easier deployment.

Deployment: Deploy the application to a cloud platform (e.g., Google Cloud Platform, Heroku, AWS).