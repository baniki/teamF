import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import re
from fake_useragent import UserAgent
ua = UserAgent()
useragent = ua.chrome

from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_path = '/Users/cerori/Documents/teamF/firstProjects/chromedriver'

options = Options()
options.add_argument('--incognito')

driver = webdriver.Chrome(executable_path=chrome_path, options=options)

url = 'https://auctions.yahoo.co.jp/search/advanced?p=&ei=UTF-8&auccat=0&slider=0&tab=cl'
driver.get(url)

sleep(3)

query = input()
search_box = driver.find_element_by_id('f0v0')
search_box.send_keys(query)
search_box.submit()

url = driver.current_url


def get_html(url):
    headers = {"User-Agent": useragent}
    response = requests.get(url, headers=headers)
    return response


item_urls = []
for _ in range(1):
    response = get_html(url)
    soup_result = bs(response.content, "html.parser")
    item_urls += [item.find(class_="Product__titleLink").get("href") for item in soup_result.findAll(class_="Product")]
    url = soup_result.find(class_="Pager__list Pager__list--next").find("a").get("href")
    print(url)
    sleep(5)
    print("*" * 110)

detail_result = []
for url in item_urls:
    res = get_html(url)
    soup = bs(res.content, "html.parser")
    detail_result.append(soup)
    sleep(1)


def details(item):
    return {
        "price": "\t".join([
            "|".join([pr.find(class_="Price__title").text.strip(), pr.find(class_="Price__value").text.strip()])
            for pr in item.findAll(class_=re.compile("Price Price--(current|buynow)"))
        ]),
        "title": item.find(class_="ProductTitle__text").text.strip(),
        "url": "".join([
            link.get("href")
            for link in item.findAll("link")
            if link.get("rel")[0] == "canonical"
        ]),
        "pictures": "|".join([pic.find("img").get("src") for pic in item.findAll(class_="ProductImage__inner")]),
        "spec_table": "\t".join([
            "|".join([dt.text.strip(), dd.text.strip()])
            for dt, dd in zip(item.find(class_="ProductDetail__body").findAll("dt"), item.find(class_="ProductDetail__body").findAll("dd"))
        ]),
        "status": "\t".join([
            "|".join([th.text.strip(), ">".join([pr.text.strip() for pr in product.findAll("li")])])
            for th, product in zip(item.find(class_="ProductTable__body").findAll("th"), item.find(class_="ProductTable__body").findAll(class_="ProductTable__items"))
        ])
    }


li = []
for item in detail_result:
    li.append(details(item))

df = pd.DataFrame(li)


def current_price(price):
    if "\t" in price:
        for pr in price.split("\t"):
            if "現在価格" in pr:
                p = re.search(r"\d+?円", pr.replace(",", "")).group()
                return int(re.sub(r"[円]", "", p))
    elif "現在価格" in price:
        p = re.search(r"\d+?円", price.replace(",", "")).group()
        return int(re.sub(r"[円]", "", p))
    return 0


def buynow_price(price):
    if "\t" in price:
        for pr in price.split("\t"):
            if "即決価格" in pr:
                p = re.search(r"\d+?円", pr.replace(",", "")).group()
                return int(re.sub(r"[円]", "", p))
    elif "即決価格" in price:
        p = re.search(r"\d+?円", price.replace(",", "")).group()
        return int(re.sub(r"[円]", "", p))
    return 0


df["current_price"] = df.price.apply(current_price)
df["buynow_price"] = df.price.apply(buynow_price)

df["item_status"] = df.status.apply(lambda x: x.split("\t")[1].split("|")[1])

df.to_csv('./data/after_scrape_results.csv')

sleep(10)

driver.quit()
