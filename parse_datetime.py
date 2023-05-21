import datetime

import requests
from bs4 import BeautifulSoup as bs


def find_city(city_name) -> str:
    response = requests.get("https://dateandtime.info/ru/country.php?code=RU")
    soup = bs(response.text, "html.parser")
    table = soup.find('table', id='city_table').find('tbody')
    for tr in table.find_all('tr'):
        name1 = tr.find_next().a.text
        name2 = tr.find_next().find_next_sibling().find_next_sibling().a.text
        if city_name.lower() == name1.lower():
            city = tr.find_next().a['href']
            return city[city.find('=') + 1:]
        elif city_name.lower() == name2.lower():
            city = tr.find_next().find_next_sibling().find_next_sibling().a['href']
            return city[city.find('=') + 1:]
    return ''


def dateandtime_param(city_name):
    id = find_city(city_name)
    duration_list = []
    for month in range(1, 13):
        response = requests.get(f"https://dateandtime.info/ru/citysunrisesunset.php?id={id}&month={month}&year=2023")
        soup = bs(response.text, "html.parser").find('section')
        table = soup.find('table', class_='sunrise_table').find('tbody')
        tr_list = table.find_all('tr')
        median = len(tr_list) // 2
        sunrise = tr_list[median].find_next().find_next_sibling().find_next().text
        sunset = tr_list[median].find_next().find_next_sibling().find_next_sibling().find_next().text
        sunrise = datetime.datetime.strptime(sunrise, '%H:%M')
        sunset = datetime.datetime.strptime(sunset, '%H:%M')
        duration = sunset - sunrise
        duration_list.append(duration.__str__())
    return duration_list



