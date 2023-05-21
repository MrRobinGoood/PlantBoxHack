import json
from flask import Flask
from flask import request
from main import get_filtered_plants
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

@app.route('/plants', methods=['POST'])
def location():
    latitude = request.json.get('latitude')
    longitude = request.json.get('longitude')
    data = get_filtered_plants(latitude, longitude)
    return data


@app.route('/plants', methods=['GET'])
def plants():
    with open('resources/database.json', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data


if __name__ == "__main__":
   app.run()