import re

import requests
from bs4 import BeautifulSoup as bs


def find_subject(sub_name: str) -> str:
    response = requests.get("https://www.plantarium.ru/page/redbooks.htmlhttp:/www.oopt.aari.ru/rbdata")
    soup = bs(response.text, "html.parser").find('table', class_='list-table')
    for td in soup.find_all('td', class_="bold")[::2]:
        if sub_name.lower() == td.a.text.lower():
            href = td.a['href']
            return href[href.rfind('/')+1:href.rfind('.')]
    return ''


def find_plant(region_name: str, plant_name: str) -> str:
    id = find_subject(region_name)
    response = requests.get(f"https://www.plantarium.ru/page/redbook/id/{id}.html")
    soup = bs(response.text, "html.parser")

    for tr in soup.find_all('tr', class_='row-state-normal row-lined'):
        names = tr.find_next().find_next_sibling().find_next_sibling().find_next_sibling().text
        names = names.split(',')
        for name in names:
            if name.lower() == plant_name.lower():
                return region_name
    return ''

