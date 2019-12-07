import lxml.html as html
import requests
from datetime import datetime
from slugify import slugify


class FlixbusScraper:
    def __init__(self):
        self.cities_codes = self.get_cities_codes()
        self.session = requests.Session()

    def get_cities_codes(self):
        r = requests.get('https://d11mb9zho2u7hy.cloudfront.net/api/v1/cities')
        cities_codes = {}
        for key, data in r.json()['cities'].items():
            cities_codes[data['slug']] = data['id']
        return cities_codes

    def get_journeys_html(self, source, destination, departure_date):
        departure_city = self.cities_codes.get(source, None)
        arrival_city = self.cities_codes.get(destination, None)
        if departure_city is None or arrival_city is None:
            raise ValueError('Cant find id for given cities')
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
                'Flixbus did not return status code {}, returned {}'.format(    
                    r.status_code)
            )
        return r.text

    def get_parsed_journeys(self, source, destination, departure_date):
        source_slug = slugify(source)
        destination_slug = slugify(destination)
        journeys_html = self.get_journeys_html(
            source_slug, destination_slug, departure_date
        )
        return self.parse_journeys(journeys_html, departure_date)

    def parse_journeys(self, html_doc, departure_date):
        doc = html.fromstring(html_doc)
        journeys_divs = doc.xpath((
            '//div[contains(@class, "ride-item-pair") and'
            'contains(@data-departure-date, "{}")]'.format(
                departure_date.strftime('%Y-%m-%d')
            )
        ))
        journeys = []
        for div in journeys_divs:
            journey = {}

            departure_hour, departure_minute = div.xpath(
                './/div[@class="departure"]'
            )[0].text.split(':')
            
            arrival_hour, arrival_minute = div.xpath(
                './/div[@class="arrival"]'
            )[0].text.split(':')
            
            dt = departure_date.replace(
                hour=int(departure_hour), minute=int(departure_minute)
            )
            if dt < datetime.now():
                # do not list journey that already started
                continue
            journey['departure_datetime'] = dt.strftime('%Y-%m-%d %H:%M:%S')

            journey['arrival_datetime'] = departure_date.replace(
                hour=int(arrival_hour), minute=int(arrival_minute)
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            journey['source'] = div.xpath(
                './/div[contains(@class, "departure-station-name")]')[0].text
            
            journey['destination'] = div.xpath(
                './/div[contains(@class, "arrival-station-name")]')[0].text
            
            journey['price'] = div.xpath(
                './/span[contains(@class, "currency-small-cents")]'
            )[0].text_content().split()[0]
            
            journeys.append(journey)
        
        return journeys


if __name__ == '__main__':
    scraper = FlixbusScraper()
    j = scraper.get_parsed_journeys('brno', 'berlin', datetime.now())
