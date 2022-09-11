# # Scraping bot Kayak flights website

import pandas as pd
import selenium
from selenium.webdriver.common.by import By
from selenium import webdriver
import numpy as np
from time import sleep
from random import randint
import datetime
import calendar


# ### Scrape the DATA

# set the urls to scrape, a year from now

year_from_now = datetime.date.today() + datetime.timedelta(days=365)
url_new = []

while year_from_now != datetime.date.today():
    end = year_from_now.replace(day=1) - datetime.timedelta(days=1)
    start = year_from_now.replace(day=1) - datetime.timedelta(days=end.day)
    monthdays = end - start
    year_from_now = year_from_now - datetime.timedelta(days=monthdays.days + 1)

    if year_from_now == datetime.date.today():
        url_new.append(
            f'https://www.kayak.com/explore/TLV-anywhere/{datetime.date.today().strftime("%Y%m%d")},{end.strftime("%Y%m%d")}'
        )
    else:
        url_new.append(
            f'https://www.kayak.com/explore/TLV-anywhere/{start.strftime("%Y%m%d")},{end.strftime("%Y%m%d")}'
        )


destenation = []
price = []
dest_list = []

# Initialize Selenium
for y in url_new:
    scrap_website = y
    driver = webdriver.Chrome()
    sleep(2)
    driver.get(scrap_website)
    sleep(20)

    html = driver.page_source
    # Scaling up the map inside the website for more flight result
    for a in range(0, 2):
        driver.find_element(
            By.XPATH,
            "/html/body/div[1]/div[1]/main/div[2]/div[2]/div[2]/div/div[1]/div/button[2]",
        ).click()
        sleep(3)
    # Load more flights
    try:
        for i in range(30):
            driver.find_element(
                By.XPATH,
                "/html/body/div[1]/div[1]/main/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[5]/button",
            ).click()
            print(i)
            sleep(randint(2, 6))

    except:
        dest = driver.find_elements(
            By.XPATH,
            "/html/body/div[1]/div[1]/main/div[2]/div[2]/div[2]/div/div[2]/div/div/div/div[3]",
        )
        print("get Data")
        # Make an ugly list
        for element in dest:
            dest_list.append(element.text)
            sleep(3)


# ### Process the DATA

# make ugly list more beautiful

for n in dest_list:
    destenation.append(n.split("\n"))

list_of = []
for dest in destenation:
    for month in dest:
        list_of.append(month)
list_of

# Check for only items with Price and return the index

import re

index_list = []
x = 0

for i in list_of:
    if re.match("from", i):
        index_list.append(x)
    x = x + 1

# make list from items with price only

final_list = []

for x in index_list:
    final_list.append(list_of[x - 1])
    final_list.append(list_of[x])
    final_list.append(list_of[x + 1])
    final_list.append(list_of[x + 2])

# ### Get Destenation

flights = pd.DataFrame()

flights["destenation"] = final_list[::4]

# ### Get contry

flights["Contry"] = final_list[2::4]

### Get Prices

prices = []
for price in final_list[1::4]:
    prices.append(price[6:])

flights["prices"] = prices

# ### Get dates

dates = []
for inout in final_list[3::4]:
    dates.append(inout.split(" "))

days_name_out = []
month_out = []
day_num_out = []
days_name_return = []
month_return = []
day_num_return = []
i = 0
for x in dates:
    days_name_out.append(x[0][0:3])
    month_out.append(x[1])
    day_num_out.append(x[2])
    days_name_return.append(x[4][0:3])
    month_return.append(x[5])
    day_num_return.append(x[6])


flights["Out day"] = days_name_out
flights["Out month"] = month_out
flights["Out date"] = day_num_out
flights["Back day"] = days_name_return
flights["Back month"] = month_return
flights["Back date"] = day_num_return

data = flights

# ### working on the DF

# concat month and the day of the month
data["Departure"] = data["Out month"] + " " + data["Out date"].astype(str)
data = data.drop(["Out month", "Out date"], axis=1)

data["Arrival"] = data["Back month"] + " " + data["Back date"].astype(str)
data = data.drop(["Back month", "Back date"], axis=1)

# convert Date str into a date object and corcting the year
from datetime import datetime

row = 0
for i in data["Departure"]:
    data["Departure"][row] = datetime.strptime(data["Departure"][row], "%b %d").date()

    if datetime.today().month <= data["Departure"][row].month <= 12:
        data["Departure"][row] = data["Departure"][row].replace(
            year=datetime.today().year
        )
        row = row + 1
    else:
        data["Departure"][row] = data["Departure"][row].replace(
            year=datetime.today().year + 1
        )
        row = row + 1

row = 0
for i in data["Arrival"]:
    data["Arrival"][row] = datetime.strptime(data["Arrival"][row], "%b %d").date()

    if datetime.today().month <= data["Arrival"][row].month <= 12:
        data["Arrival"][row] = data["Arrival"][row].replace(year=datetime.today().year)
        row = row + 1
    else:
        data["Arrival"][row] = data["Arrival"][row].replace(
            year=datetime.today().year + 1
        )
        row = row + 1

# add number of days staying
data["# of days"] = data["Arrival"] - data["Departure"]

# conver Weekday str to date object
for i in range(len(data["Out day"])):
    data["Out day"][i] = data["Departure"][i].strftime("%A")
for i in range(len(data["Back day"])):
    data["Back day"][i] = data["Arrival"][i].strftime("%A")

# convert price to int
for i in range(len(data["prices"])):
    data["prices"][i] = int(data["prices"][i].replace(",", ""))

# Save the data as CSV file
data.to_csv("kayakflights.csv", index=False)
