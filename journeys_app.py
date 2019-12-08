import json
from flask import Flask, jsonify, request, render_template, make_response
from sqlalchemy.orm import aliased

from flix_scraper import FlixbusScraper
from forms import SearchForm
from connections import is_valid_date
from db.db_config import session
from db.models import Journey


app = Flask(__name__)
scraper = FlixbusScraper()


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({'message': str(e)}), 400


@app.route('/api/search', methods=['GET'])
def search_api():
    params = dict(request.args)
    source = params.pop('source', None)
    destination = params.pop('destination', None)
    departure_date = params.pop('departure_date', None)
    if None in [source, destination, departure_date]:
        return jsonify({'message': 'missing required parameter'}), 400

    dt = is_valid_date(departure_date)
    journeys = scraper.get_parsed_journeys(source, destination, dt, **params)
    return jsonify(journeys), 200


@app.route('/api/combinations', methods=['GET'])
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

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm(csrf_enabled=False)
    if form.validate_on_submit():
        journeys = scraper.get_parsed_journeys(
            form.source.data, form.destination.data, form.date.data)
        template = render_template('search.html', journeys=journeys, form=form)
        return make_response(template)
    return render_template('search.html', form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
