import json
from flask import Flask, jsonify, request

from flix_scraper import FlixbusScraper
from connections import is_valid_date


app = Flask(__name__)
scraper = FlixbusScraper()


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({'message': str(e)}), 400


@app.route('/search', methods=['GET'])
def search():
    params = dict(request.args)
    source = params.pop('source', None)
    destination = params.pop('destination', None)
    departure_date = params.pop('departure_date', None)
    if None in [source, destination, departure_date]:
        return jsonify({'message': 'missing required parameter'}), 400

    dt = is_valid_date(departure_date)
    journeys = scraper.get_parsed_journeys(source, destination, dt, **params)
    return jsonify(journeys), 200



if __name__ == '__main__':
    app.run(debug=True)
