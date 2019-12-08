import json
from flask import Flask, jsonify, request
from sqlalchemy.orm import aliased

from flix_scraper import FlixbusScraper
from connections import is_valid_date
from db.db_config import session
from db.models import Journey


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


@app.route('/combinations', methods=['GET'])
def combinations():
    source = request.args.get('source', None)
    destination = request.args.get('destination', None)
    date = request.args.get('date', None)
    if None in [source, destination, date]:
        return jsonify({'message': 'missing requred parameter'}), 400

    dt = is_valid_date(date)
    j1, j2 = aliased(Journey), aliased(Journey)
    journeys = []
    for segment_1, segment_2 in (
        session.query(j1, j2).filter(
            (j1.source == source) & (j2.destination == destination)
            & (j1.destination == j2.source)
            & (j1.arrival_datetime < j2.departure_datetime)
        ).all()
    ):
        journeys.append({
            "source": segment_1.source,
            "destination": segment_2.destination,
            "departure": segment_1.departure_datetime.isoformat(),
            "arrival": segment_2.arrival_datetime.isoformat(),
        })

    return jsonify(journeys), 200


if __name__ == '__main__':
    app.run(debug=True)
