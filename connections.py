import argparse
import requests
from datetime import datetime
from pprint import pprint

from flix_scraper import FlixbusScraper

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=str)
    parser.add_argument('--destination', required=True, type=str)
    parser.add_argument('--departure_date', required=True, type=is_valid_date)
    return parser.parse_args()


def is_valid_date(arg):
    try:
        return datetime.strptime(arg, '%Y-%d-%m')
    except ValueError:
        raise argparse.ArgumentTypeError(
            'Not a valid date format {}'.format(arg)
        )


if __name__ == '__main__':
    args = parse_args()
    scraper = FlixbusScraper()
    journeys = scraper.get_parsed_journeys(
        args.source, args.destination, args.departure_date
    )
    pprint(journeys)

    
