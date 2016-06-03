from splinter import Browser
import splinter.exceptions
import datetime
import time
import csv
import re
import json
import urllib.request
import os
import dateutil.parser
import time
import pandas as pd


current_dir = os.path.dirname(__file__)


duration_regex = re.compile(r'((?P<hours>\d+?)h)? ((?P<minutes>\d+?)m)?')

# class CustomJSONEncoder(JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, Airport):
#             return obj.to_dict()
#         if isinstance(obj, Flight):
#             return obj.to_dict()
#         else:
#             JSONEncoder.default(self, obj)

# app.json_encoder = CustomJSONEncoder




# class Airport(db.Model):
#     __tablename__ = "airport"
#     code = db.Column(db.String(3), primary_key=True)
#     name = db.Column(db.String(80), unique=True)
#     timezone = db.Column(db.String(80), unique=False)

#     def __init__(self, code, name, timezone):
#         self.code = code
#         self.name = name
#         self.timezone = timezone

#     def to_dict(self):
#         return {"code" : self.code, "name" : self.name, "timezone" : self.timezone}

#     @classmethod
#     def from_json(cls, json_str):
#         code     = json_str["code"]
#         name     = json_str["name"]
#         timezone = json_str["timezone"]
#         return Airport(code, name, timezone)

#     def __repr__(self):
#         return '<Airport %r>' % self.name

# class Flight(db.Model):
#     __tablename__ = "flight"
#     id = db.Column(db.Integer, primary_key=True)
#     parent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     #origin_airport = db.Column(db.String(80), unique=False)
#     #destination_airport = db.Column(db.String(80), unique=False)
#     origin_aiirport = db.relationship("Airport")
#     departure = db.Column(db.DateTime, unique=False)
#     arrival = db.Column(db.DateTime, unique=False)
#     flight_numbers = db.Column(db.String(80), unique=False)
#     routing = db.Column(db.String(80), unique=False)
#     price = db.Column(db.String(80), unique=False)


#     def __init__(self, origin_airport, destination_airport, departure, arrival, flight_numbers, routing, price):
#         self.origin_airport = origin_airport
#         self.destination_airport = destination_airport
#         self.departure = departure
#         self.arrival = arrival
#         self.flight_numbers = flight_numbers
#         self.routing = routing
#         self.price = price

#     def to_dict(self):
#         return {"origin_airport" : self.origin_airport,
#                 "destination_airport" : self.destination_airport,
#                 "departure" : self.departure.isoformat(),
#                 "arrival" : self.arrival.isoformat(),
#                 "flight_numbers" : self.flight_numbers,
#                 "routing" : self.routing,
#                 "price" : self.price
#                 }

#     @classmethod
#     def from_json(cls, json_str):
#         origin_airport      = Airport.from_json(json_str["origin_airport"])
#         destination_airport  = Airport.from_json(json_str["destination_airport"])
#         departure           = dateutil.parser.parse(json_str["departure"])
#         arrival             = dateutil.parser.parse(json_str["arrival"])
#         flight_numbers      = json_str["flight_numbers"]
#         routing             = json_str["routing"]
#         price               = json_str["price"]
#         return Flight(origin_airport, destination_airport, departure, arrival, flight_numbers, routing, price)


# class User(db.Model, UserMixin):
#     __tablename__ = "user"
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String)
#     email = db.Column(db.String, unique=True)
#     username = db.Column(db.String, unique=True)
#     password = db.Column(db.String)
#     flights = db.relationship("Flight")


def parse_duration(time_str):
    parts = duration_regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    return datetime.timedelta(**time_params)


def index_containing_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
              return i
    return None


def get_sw_airports():
    """Scrape the airports from the southwest site to save and create DB"""
    browser = Browser('phantomjs')
    airport_strs = []
    url = 'https://www.southwest.com/html/air/airport-information.html'

    try:
        browser.visit(url)
        airports = browser.find_by_css('.airport_name')
        for airport in airports:
            airport_strs.append([airport.text])
    except:
        pass

    return airport_strs

def save_sw_airports():
    """Save the airports to a CSV file for the js typeahead to use """
    air = get_sw_airports()
    if air is not None:
        with open(current_dir+'/static/airports.csv', 'w') as csvfile:
            air_writer = csv.writer(csvfile, quoting = csv.QUOTE_MINIMAL, delimiter=';',quotechar='|')
            air_writer.writerows(air)

def get_iata_tz_map():
    """Get a mapping from iata code to the timezone of the airport"""
    url = 'https://raw.githubusercontent.com/hroptatyr/dateutils/tzmaps/iata.tzmap'
    iata_tz_map = []
    try:
        response = urllib.request.urlopen(url)
        data = response.read()
        text = data.decode('utf-8')
        for iata_tz in text.splitlines():
            iata, tz = iata_tz.strip().split("\t")
            iata_tz_map.append((iata,tz))
    except:
        pass
    return iata_tz_map

def save_iata_tz_map():
    tz_map = get_iata_tz_map()
    if tz_map is not None:
        with open(current_dir+'/static/airports_timezones.csv', 'w', newline='') as csvfile:
            tz_writer = csv.writer(csvfile)
            tz_writer.writerows(tz_map)



def get_flights(origin_airport_code, destination_airport_code, departure_date_str):

    browser = Browser('phantomjs')
    browser.visit('https://www.southwest.com/')

    booking_button = browser.find_by_id('booking-form--flight-tab')[0]
    booking_button.click()

    #if return_date:
    #    browser.choose('twoWayTrip','true')
    #else:
    browser.choose('twoWayTrip','false')
    #departure_date_str = departure_date.strftime("%m/%d/%y")

    # works better with the date selected first... no idea why.
    browser.execute_script("document.getElementsByName('outboundDateString')[0].type = 'visible'")
    time.sleep(2)
    browser.fill('originAirport', origin_airport_code)
    browser.fill('destinationAirport', destination_airport_code)
    browser.fill('outboundDateString', departure_date_str)

    submit_button = browser.find_by_id('jb-booking-form-submit-button')[0]
    submit_button.click()

    flights_DOM_table = browser.find_by_css('.bugTableRow')
    flights_table = []

    for flight_DOM in flights_DOM_table:
        depart_time = flight_DOM.find_by_css('.depart_column .time').text
        depart_time = depart_time.zfill(5)
        depart_am_pm = flight_DOM.find_by_css('.depart_column .indicator').text
        duration = parse_duration(flight_DOM.find_by_css('.duration').text)
        depart_str = departure_date_str + ", " + depart_time + depart_am_pm
        departure = datetime.datetime.strptime(depart_str, "%m/%d/%y, %I:%M%p")
        arrival = departure + duration

        #arrive_time = flight_DOM.find_by_css('.arrive_column .time').text
        #arrive_am_pm = flight_DOM.find_by_css('.arrive_column .indicator').text

        flight_nums = flight_DOM.find_by_css('.bugLinkText') # could be a few of these
        f = []
        for num in flight_nums:
            f.append(num.text[0:-14])
        routing = flight_DOM.find_by_css('.bugLinkRouting').text[0:-14]
        if len(f) > 1:
            routing += " - " + flight_DOM.find_by_css('.search-results--flight-stops').text
        box = flight_DOM.find_by_css('.price_column')[2] # only the wanna get away
        #check if sold out, unavailable or available
        price = None
        try:
            price = box.find_by_css('label.product_price')[0].text[1:] #strips the currency symbol
        except splinter.exceptions.ElementDoesNotExist:
            pass
        try:
            price = box.find_by_css('.insufficientInventory')[0].text.strip()
        except splinter.exceptions.ElementDoesNotExist:
            pass
        try:
            price = box.find_by_css('.unqualifiedForAnyFare')[0].text.strip()
        except:
            pass
        flight = (origin_airport_code, destination_airport_code, departure, arrival, tuple(f), routing, price)
        flights_table.append(flight)

    return flights_table


def price_check(origin_airport_code, destination_airport_code, departure_date, flight_numbers):
    headers = ["from","to","departure", "arrival", "flight_nums", "routing", "price"]
    flights = get_flights(origin_airport_code,destination_airport_code,departure_date)
    df = pd.DataFrame(flights, columns=headers)
    #print(df)
    return df[df.flight_nums == flight_numbers].price.item())


# def price_check(origin_airport_code, destination_airport_code, departure_date, flight_numbers):

#     browser = Browser('phantomjs')
#     browser.visit('https://www.southwest.com/')

#     booking_button = browser.find_by_id('booking-form--flight-tab')[0]
#     booking_button.click()
#     #date_str = departure_date.strftime("%m/%d/%y")
#     date_str = departure_date

#     #if return_date:
#     #    browser.choose('twoWayTrip','true')
#     #else:
#     browser.choose('twoWayTrip','false')

#     # works better with the date selected first... no idea why.
#     browser.execute_script("document.getElementsByName('outboundDateString')[0].type = 'visible'")
#     browser.fill('originAirport', origin_airport_code)
#     browser.fill('destinationAirport', destination_airport_code)
#     browser.fill('outboundDateString', date_str)

#     submit_button = browser.find_by_id('jb-booking-form-submit-button')[0]
#     submit_button.click()

#     #flight_num_table = browser.find_by_css('a.bugLinkText')
#     flight_num_column = browser.find_by_css('span.swa_td_flightNumber')
#     #for flight in flight_list:
#     #    print(flight.text.)
#     table_row = None
#     for i, s in enumerate(flight_num_column):
#         #print(s.text)
#         if all([flight_number in s.text for flight_number in flight_numbers]):
#             #if flight_number in s.text:
#             table_row = i

#     if table_row is None:
#         raise ValueError('Flight number not in list')

#     #print("table row: {}".format(table_row))

#     #select row
#     table = browser.find_by_css('#faresOutbound')
#     row = table.find_by_css('tr#outbound_flightRow_{}'.format(table_row+1))
#     box = row.find_by_css('td.price_column')[2] # only the wanna get away
#     price = box.find_by_css('label.product_price')[0].text[1:] #strips the currency symbol

#     return int(price)


def check_in(self, conf_number, first_name, last_name):

    browser.visit('https://www.southwest.com/')

    checkin_form_button = browser.find_by_id('booking-form--check-in-tab')[0]
    checkin_form_button.click()

    browser.fill('confirmationNumber', conf_number)
    browser.fill('firstName', first_name)
    browser.fill('lastName', last_name)

    checkin_button = browser.find_by_id('jb-button-check-in')[0]
    checkin_button.click()

    submit_button = browser.find_by_id('submitButton')[0]
    submit_button.click()




