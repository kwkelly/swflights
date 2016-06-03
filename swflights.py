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

duration_regex = re.compile(r'((?P<hours>\d+?)h)? ((?P<minutes>\d+?)m)?')

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
    browser.execute_script("document.getElementsByName('outboundDateString')[0].type = 'visible'")
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
    # need to check that we find one
    try:
        price = df[df.flight_nums == flight_numbers].price.item()
    except:
        raise ValueError("Could not get price from that flight")
    return price

def check_in(self, conf_number, first_name, last_name):

    browser = Browser('phantomjs')
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




