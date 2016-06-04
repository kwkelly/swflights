import swflights
import pandas as pd
import csv
import datetime
import numpy as np
import splinter.exceptions
import time
import string
import datetime
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
import smtplib
import email_config
import logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import click

# logging - http://victorlin.me/posts/2012/08/26/good-logging-practice-in-python
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('swprices.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


Base = declarative_base()

class Flight(Base):
    __tablename__ = 'flights'
    id = Column(Integer, primary_key=True)
    origin_airport_code = Column(String)
    destination_airport_code = Column(String)
    date = Column(String)
    flight_nums = Column(String)
    alert_price = Column(String)
    email_addr = Column(String)
    emailed = Column(Boolean, default=False)

    def __init__(self,origin_airport_code, destination_airport_code, date, flight_nums, alert_price, email_addr):
        self.origin_airport_code = origin_airport_code
        self.destination_airport_code = destination_airport_code
        self.date = date
        self.flight_nums = flight_nums
        self.alert_price = alert_price
        self.email_addr = email_addr

    def __repr__(self):
        return "id={}, origin={}, dest={}, date={}, nums={}, alert={}, email_addr={}, emailed={}".format(
                                                            self.id,
                                                            self.origin_airport_code,
                                                            self.destination_airport_code,
                                                            self.date,
                                                            self.flight_nums,
                                                            self.alert_price,
                                                            self.email_addr,
                                                            self.emailed)

    def __str__(self):
        return "id={}, origin={}, dest={}, date={}, nums={}, alert={}, email_addr={}, emailed={}".format(
                                                            self.id,
                                                            self.origin_airport_code,
                                                            self.destination_airport_code,
                                                            self.date,
                                                            self.flight_nums,
                                                            self.alert_price,
                                                            self.email_addr,
                                                            self.emailed)

engine = create_engine('sqlite:///flights.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


cli = click.Group()

@cli.command()
def create_table():
    """Creates the table. Necessary for all other actions"""
    Base.metadata.create_all(engine)

@cli.command()
def add():
    """This adds a flight to be checked"""
    origin_airport_code = input("Origin Code (ex: AUS): ")
    destination_airport_code = input("Destination Code: ")
    departure_date = input("Departure Date (MM/DD/YY): ")
    flight_nums = input("Flight Numbers (ex: num1,num2): ")
    alert_price = input("Alert Price: ")
    email_addr = input("Email Address: ")
    f = Flight(origin_airport_code, destination_airport_code, departure_date, flight_nums, alert_price, email_addr)
    session.add(f)
    session.commit()

@cli.command()
def ls():
    """This lists all the flights currently in our system"""
    for instance in session.query(Flight).order_by(Flight.id):
        print(instance)


def send_alert(origin_airport_code, destination_airport_code, departure_date, flight_nums, price, email_addr):
    # http://naelshiab.com/tutorial-send-email-python/
    try:
        server = smtplib.SMTP(email_config.server, email_config.port)
        server.starttls()
        server.login(email_config.email, email_config.password)

        msg = MIMEText("Your Southwest Airlines flight from {} to {} on {} (flight numbers: [{}]) is now priced at ${}. ".format(
                        origin_airport_code, destination_airport_code, departure_date, ",".join(flight_nums), price))
        msg["From"] = email_config.email
        msg["To"] = email_addr
        msg["Subject"] = "Southwest Airlines Price Alert"
        text = msg.as_string()
        server.sendmail(email_config.email, email_addr, text)
        server.quit()
        logger.info('Price alert email sent to {}'.format(email_addr))
    except Exception as e:
        logger.error('Failed to send email', exc_info=True)


@cli.command()
def check_flights():
    """This checks the flight prices agains your alert price"""
    for flight in session.query(Flight).order_by(Flight.id):
        origin_airport_code = flight.origin_airport_code
        destination_airport_code = flight.destination_airport_code
        departure_date = flight.date
        flight_nums = tuple(flight.flight_nums.split(','))
        alert_price = int(flight.alert_price)
        email_addr = flight.email_addr
        emailed = flight.emailed


        # try to get the price information for the flights in the csv file
        for i in range(5):
            try:
                price = swflights.price_check(origin_airport_code,destination_airport_code,departure_date,flight_nums)
                timestamp = datetime.datetime.now().strftime('%m/%d/%y %H:%M')
            except Exception as e:
                logger.error('Failed to get price.', exc_info=True)
                time.sleep(30)
                continue
            break
        try:
            price = int(price)
        except ValueError:
            # price is probably unavailable or some other one
            price = np.nan

        # log the flight prices
        file_name = "{}_{}_{}_{}.txt".format(origin_airport_code,
                                        destination_airport_code,
                                        departure_date.replace("/","-"),
                                        "_".join(flight_nums))
        with open(file_name, "a") as f:
            f.write("{} {}\n".format(timestamp, price))

        if (price < alert_price) and not emailed:
            send_alert(origin_airport_code, destination_airport_code, departure_date, flight_nums, price, email_addr)
            flight.emailed = True
            session.commit()

if __name__ == "__main__":
    cli()
