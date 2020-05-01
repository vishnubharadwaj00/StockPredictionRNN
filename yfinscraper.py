from bs4 import BeautifulSoup
import requests
import re
import time
import random
import sys
import numpy as np
import pandas as pd
from selenium import webdriver
import chromedriver_binary
from selenium.webdriver.common.keys import Keys

url = 'https://finance.yahoo.com/quote/TSLA/history?p=TSLA'

user_agent = {'User-agent': 'Mozilla/5.0'}
response = requests.get(url, headers=user_agent)

driver = webdriver.Chrome(executable_path="/home/vishnub/chromedriver")
driver.get(url)
for i in range(0, 50):
    elem = driver.find_element_by_tag_name('a')
    elem.send_keys(Keys.PAGE_DOWN)

html = driver.execute_script('return document.body.innerHTML;')
soup = BeautifulSoup(html, 'lxml')

close_price = [entry.text for entry in soup.find_all(
    'span', {'class': 'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)'})]
after_hours_price = [entry.text for entry in soup.find_all(
    'span', {'class': 'C($primaryColor) Fz(24px) Fw(b)'})]

tbl = soup.find('table', {"class": "W(100%) M(0)"})
df = pd.read_html(str(tbl))[0]
print(close_price, after_hours_price)
print(df)

# removing last row which has unwanted text and first column with index
df.drop(df.tail(1).index, inplace=True)

df.to_csv("tsla.csv")
