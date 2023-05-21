import pymorphy2
from nltk.tokenize import word_tokenize
import PyPDF2
import re
import json
from resources.dataset import PLANT_NAMES, LIST_SOIL, LIST_SOIL_REAL
from resources.find_dicts import RUSSIA_SUBJECTS as RS, KEYS_AREA, AREAS, KEYS_SUBJECT, FULL_RUSSIA_SUBJECTS, PERIOD, \
    KEYS_SOWING, KEYS_COLLECTING

from parse_redbook import find_plant
from parse_datetime import dateandtime_param

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="app")

# import nltk
# nltk.download('punkt')

morph = pymorphy2.MorphAnalyzer()


def get_key(d, value):
    for k, v in d.items():
        if v == value:
            return k


def get_plants_name_and_pages(reader):
    plant_names = []
    num_pages = []
    for i in range(5, 18):
        page = reader.pages[i]
        text = page.extract_text()
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if re.search(r"\d+", line):
                num_page = int(re.findall(r"\d{2,}", line)[0])
                num_pages.append(num_page)
            if re.search(r"[А-Я]{2,}", line) and not (re.search(r"[A-Z]", line)):
                line_copy = line.replace(" ", '')
                if line_copy in PLANT_NAMES.values():
                    line_copy = get_key(PLANT_NAMES, line_copy)
                    plant_names.append(line_copy)
                else:
                    plant_names.append(line)

    return plant_names, num_pages


def get_plant_page(reader, num_pages, index):
    # далее работа с каждым растением
    plant_pages = []
    plant_page = []
    for j in range(num_pages[index], num_pages[index + 1]):
        page = reader.pages[j - 1]
        text = page.extract_text()
        plant_page += get_normal_form(text)
    plant_pages.extend(plant_page)
    return plant_pages


def get_normal_form(text):
    tokens = word_tokenize(text, language="russian")
    lemma_tokens = []
    i = 0
    while i < len(tokens):
        p = morph.parse(tokens[i])[0]
        word = p.normal_form
        if word == '-' and i < len(tokens) - 1 and i != 0:
            word = tokens[i - 1] + morph.parse(tokens[i + 1])[0].normal_form
            i += 1
        lemma_tokens.append(word)
        i += 1
    return lemma_tokens


def get_filtered_plants(latitude, longitude):
    location = geolocator.reverse(f"{latitude},{longitude}")
    address = location.address.split(',')
    if address[-1].strip() != 'Россия':
        return []
    full_area = address[-3].strip()
    find_city = address[-4].strip()
    find_area = full_area.split()[0]
    with open('resources/database.json', encoding='utf-8') as json_file:
        data = json.load(json_file)
        result = []
        for i in range(len(data)):
            if (find_city in data[i].get('subjects')) or (find_area in data[i].get('areas')):
                result.append(data[i])
        return result



def upcase_first_letter(s):
    return s[0].upper() + s[1:]


def find_sowing_period(plant_page):
    keys_speriod_ids = []
    speriod_ids = []
    for i in range(len(plant_page)):

        for key in KEYS_SOWING:
            if plant_page[i] == key:
                keys_speriod_ids.append(i)

        for month in PERIOD:
            if plant_page[i] == month:
                speriod_ids.append(i)

    result_periods = set()
    for a_idx in keys_speriod_ids:
        for s_idx in speriod_ids:
            if (abs(a_idx - s_idx)) < 150:
                result_periods.add(upcase_first_letter(plant_page[s_idx]))
    return list(result_periods)


def find_collecting_period(plant_page):
    keys_cperiod_ids = []
    cperiod_ids = []
    for i in range(len(plant_page)):

        for key in KEYS_COLLECTING:
            if plant_page[i] == key:
                keys_cperiod_ids.append(i)

        for month in PERIOD:
            if plant_page[i] == month:
                cperiod_ids.append(i)

    result_periods = set()
    for a_idx in keys_cperiod_ids:
        for s_idx in cperiod_ids:
            if (abs(a_idx - s_idx)) < 150:
                result_periods.add(upcase_first_letter(plant_page[s_idx]))
    return list(result_periods)


def find_areas(plant_page):
    keys_area_ids = []
    areas_ids = []
    for i in range(len(plant_page)):

        for key in KEYS_AREA:
            if plant_page[i] == key:
                keys_area_ids.append(i)

        for area in AREAS:
            if plant_page[i] == area:
                areas_ids.append(i)

    result_areas = set()
    for a_idx in keys_area_ids:
        for s_idx in areas_ids:
            if (abs(a_idx - s_idx)) < 150:
                result_areas.add(upcase_first_letter(plant_page[s_idx]) + ' округ')
    return list(result_areas)


def find_subject(plant_page):
    subjects = RS.keys()
    keys_subject_ids = []
    subject_ids = []

    for i in range(len(plant_page)):

        for key in KEYS_SUBJECT:
            if plant_page[i] == key:
                keys_subject_ids.append(i)

        for subject in subjects:
            if plant_page[i] == subject:
                subject_ids.append(i)

    result_subjects = set()
    for a_idx in keys_subject_ids:
        for s_idx in subject_ids:
            if (abs(a_idx - s_idx)) < 150:
                result_subjects.add(FULL_RUSSIA_SUBJECTS.get(plant_page[s_idx]))
    return list(result_subjects)


def find_soil(plant_pages):
    count_next_word = 0
    previous_300_word = []
    plant_soil = []
    for page in plant_pages:
        if count_next_word > 0:
            page = page[0:count_next_word]
            count_next_word = 0
        else:
            if 'экология' in page or 'почва' in page:
                if 'почва' in page:
                    index_ecology = page.index('почва')
                    if index_ecology + 300 >= len(page):
                        count_next_word = index_ecology + 300 - len(page) + 1
                        end = len(page)
                    else:
                        end = index_ecology + 300
                    if index_ecology - 300 < 0:
                        start = 0
                        if previous_300_word:
                            page = previous_300_word[300 - index_ecology:300]
                            page_soil = get_soil_page(page)
                            for soil in page_soil:
                                plant_soil.append(' '.join(soil))
                    else:
                        start = index_ecology - 300
                else:
                    index_ecology = page.index('экология')
                    if index_ecology + 300 >= len(page):
                        count_next_word = index_ecology + 300 - len(page) + 1
                        end = len(page)
                    else:
                        end = index_ecology + 300
                    if index_ecology - 300 < 0:
                        start = 0
                        if previous_300_word:
                            page = previous_300_word[300 - index_ecology:300]
                            page_soil = get_soil_page(page)
                            for soil in page_soil:
                                plant_soil.append(' '.join(soil))
                    else:
                        start = index_ecology - 300
                previous_300_word = page[-300:]
                page = page[start:end]
            else:
                previous_300_word = []
                continue
        page_soil = get_soil_page(page)
        for soil in page_soil:
            plant_soil.append(' '.join(soil))
    return plant_soil


def get_soil_page(page):
    page_soil = []
    for i in range(len(LIST_SOIL)):
        page_copy = page.copy()
        count_delete = 0
        while LIST_SOIL[i][0] in page_copy:
            index_0 = page_copy.index(LIST_SOIL[i][0]) + count_delete
            if LIST_SOIL[i][:] == page[index_0: index_0 + len(LIST_SOIL[i])]:
                page_soil.append(LIST_SOIL_REAL[i][:])
                break
            del page_copy[page_copy.index(LIST_SOIL[i][0])]
            count_delete += 1
    return page_soil


if __name__ == '__main__':
    with open('resources/Атлас 2021.pdf', 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        plant_names, num_pages = get_plants_name_and_pages(reader)
        all_plants = []
        for j in range(195):
            result_plant = {}
            plant_page = get_plant_page(reader, num_pages, j)

            result_plant['plant_name'] = upcase_first_letter(plant_names[j].lower())

            result_plant['areas'] = find_areas(plant_page)

            result_plant['subjects'] = find_subject(plant_page)

            result_plant['soil'] = find_soil([plant_page])

            result_plant['sowing_period'] = find_sowing_period(plant_page)

            result_plant['collecting_period'] = find_collecting_period(plant_page)

            result_plant['day_length'] = []
            result_plant['redbook_subject'] = []
            result_plant['in_redbook'] = 'Нет'

            with open('resources/datetime.json', encoding='utf-8') as json_file:
                data = json.load(json_file)

            for subject in result_plant['subjects']:

                subject_key = get_key(FULL_RUSSIA_SUBJECTS, subject)
                central_city = RS.get(subject_key)
                result_plant['day_length'].append(data[subject])

                result = find_plant(subject, result_plant['plant_name'])
                if result:
                    result_plant['in_redbook'] = 'Да'
                    result_plant['redbook_subject'].append(result)

            print(j)
            all_plants.append(result_plant)
    with open('resources/database2.json', 'w', encoding='utf-8') as outfile:
        json.dump(all_plants, outfile)
    print(all_plants)
