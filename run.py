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
        print("Email alert sent to {}".format(email_addr))
    except Exception as e:
        print(e)


with open('flights.csv', newline='') as csvfile:
    flight_reader = csv.reader(csvfile, delimiter=';', quotechar='|')
    next(flight_reader)
    for flight in flight_reader:
        origin_airport_code = flight[0]
        destination_airport_code = flight[1]
        departure_date = flight[2]
        flight_nums = tuple(flight[3].split(','))
        alert_price = int(flight[4])
        email_addr = flight[5]

        # try to get the price information for the flights in the csv file
        for i in range(5):
            try:
                price = swflights.price_check(origin_airport_code,destination_airport_code,departure_date,flight_nums)
                timestamp = datetime.datetime.now().strftime('%m/%d/%y %H:%M')
            except Exception as e:
                print(e)
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
            f.write("{} {}".format(timestamp, price))

        if price < alert_price:
            send_alert(origin_airport_code, destination_airport_code, departure_date, flight_nums, price, email_addr)




# headers = ["from","to","departure", "arrival", "flight_nums", "routing", "price"]
# flights = swflights.get_flights("AUS","DCA","06/28/16")
# df = pd.DataFrame(flights, columns=headers)
# print(df.to_json())
#swflights.price_check("AUS","DCA","06/28/16",("2965",))
#print(df)
#print(df[df.flight_nums == ("2932","3596")])
