import swflights
import pandas as pd

#headers = ["from","to","departure", "arrival", "flight_nums", "routing", "price"]
#flights = swflights.get_flights("AUS","DCA","06/28/16")
swflights.price_check("AUS","DCA","06/28/16",("2965",))
#df = pd.DataFrame(flights, columns=headers)
#print(df)
#print(df[df.flight_nums == ("2932","3596")])
