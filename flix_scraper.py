import json
import lxml.html as html
from redis import StrictRedis
import requests
from datetime import datetime
from slugify import slugify


class FlixbusScraper:
    def __init__(self):
        self.session = requests.Session()
        redis_config = {
            'host': 'redis.pythonweekend.skypicker.com',
        }
        self.redis = StrictRedis(
            socket_connect_timeout=3, decode_responses=True, **redis_config
        )

    def get_cities_codes(self):
        """ Fetch flixbus codes for cities """ 
        r = self.session.get('https://d11mb9zho2u7hy.cloudfront.net/api/v1/cities')
        cities_codes = {}
        for key, data in r.json()['cities'].items():
            cities_codes[data['slug']] = data['id']
        return cities_codes

    def get_city_id(self, city):
        """
        Tries to fetch city id from redis first, if not found gets in from
        flixbus api, stores it to redis and returns it
        """
        city_redis_slug = f'letovanec:location:{city}'
        city_id = self.redis.get(city_redis_slug)
        if city_id is None:
            # city is not in redis
            cities_codes = self.get_cities_codes()
            city_id = cities_codes.get(city, None)
            if city_id is None:
                raise ValueError('Cant find id for given cities')
            self.redis.set(city_redis_slug, str(city_id), ex=60)
        return city_id

    def get_journeys_html(self, source, destination, departure_date):
        """
        Fetch flixbus search result for given source, destination
        and departure time
        """
        departure_city = self.get_city_id(source)
        arrival_city = self.get_city_id(destination)
        params = {
            'departureCity': departure_city,
            'arrivalCity': arrival_city,
            'rideDate': departure_date.strftime('%d.%m.%Y'),
            'adult': '1'
        }
        r = self.session.get(
            'https://shop.global.flixbus.com/search', params=params
        )
        if not r.ok:
            raise Exceception(
                f'Flixbus did not return status code 200, returned {r.status_code}'
            )
        return r.text

    def get_parsed_journeys(self, source, destination, departure_date):
        """
        Tries to fetch journey specidied by source, destination
        and departure date from redis. If its not there scrapes
        flixbus search result page, stores it to redis and returns
        list of journeys.
        """
        source_slug = slugify(source)
        destination_slug = slugify(destination)
        dt = departure_date.strftime('%Y-%m-%d')
        journey_slug = \
            f'letovanec:journey:{source_slug}_{destination_slug}_{dt}'
        journeys = self.redis.get(journey_slug)
        if journeys:
            # return journey if found in redis
            return json.loads(journeys)
        
        # if not found scrate flixbus and save to redis
        journeys_html = self.get_journeys_html(
            source_slug, destination_slug, departure_date
        )
        journeys = self.parse_journeys(journeys_html, departure_date)
        self.redis.set(journey_slug, json.dumps(journeys), ex=60)
        return journeys

    def parse_journeys(self, html_doc, departure_date):
        """
        Parse search result from flixbus, returns list of parsed
        journeys.
        """
        doc = html.fromstring(html_doc)
        journeys_divs = doc.xpath((
            '//div[contains(@class, "ride-item-pair") and'
            'contains(@data-departure-date, "{}")]'.format(
                departure_date.strftime('%Y-%m-%d')
            )
        ))
        journeys = []
        for div in journeys_divs:
            journey = self.parse_journey(div, departure_date)
            if journey:
                journeys.append(journey)
        
        return journeys

    def parse_journey(self, div, departure_date):
        """ Parses div that corresponds to one journey. """
        journey = {}
        departure_hour, departure_minute = \
            div.xpath('.//div[@class="departure"]')[0].text.split(':')
        
        arrival_hour, arrival_minute = \
            div.xpath('.//div[@class="arrival"]')[0].text.split(':')
        
        dt = departure_date.replace(
            hour=int(departure_hour), minute=int(departure_minute)
        )
        if dt < datetime.now():
            # do not list journey that already started
            return None
        journey['departure_datetime'] = dt.strftime('%Y-%m-%d %H:%M:%S')

        journey['arrival_datetime'] = departure_date.replace(
            hour=int(arrival_hour), minute=int(arrival_minute)
        ).strftime('%Y-%m-%d %H:%M:%S')
        
        journey['source'] = div.xpath(
            './/div[contains(@class, "departure-station-name")]')[0].text
        
        journey['destination'] = div.xpath(
            './/div[contains(@class, "arrival-station-name")]')[0].text
        
        journey['price'] = float(div.xpath(
            './/span[contains(@class, "currency-small-cents")]'
        )[0].text_content().split()[0])

        return journey

if __name__ == '__main__':
    scraper = FlixbusScraper()
    j = scraper.get_parsed_journeys('brno', 'berlin', datetime.now())
