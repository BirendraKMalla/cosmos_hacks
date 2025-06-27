from flask import Flask, request, jsonify, send_from_directory
import requests
import os

app = Flask(__name__)

API_KEY = "0197beddca2d709d17cf5b524a6b708a"

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/get_aqi', methods=['GET'])
def get_aqi():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)