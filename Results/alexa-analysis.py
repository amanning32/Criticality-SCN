import json
import csv

import tldextract

alexa_json = None
old_alexa_json = None
country_code_map = None
country_pop_map = {}
internet_percent_map = {}
internet_population_dict = {}
internet_total_percent_dict = {}
internet_population_total = 0

def find_country_from_code(code: str) -> str:
    for country, c_code in country_code_map.items():
        if code == c_code:
            return country

    return None

def find_code_from_country(country: str) -> str:
    if country in country_code_map:
        return country_code_map[country]

    for key in country_code_map:
        if country in key:
            return country_code_map[key]

    # print(f"No country code found for {country}")
    return None

with open('../Crawling/alexa_top_50_20220407.json', 'r') as f:
    alexa_json = json.load(f)

with open('../Crawling/alexa_top_50_20200215.json', 'r') as f:
    old_alexa_json = json.load(f)

with open('../Geolocation/serv_data/country_name_code.json', 'r') as f:
    country_code_map = json.load(f)

def create_population_files():
    with open('data/total_population.csv', 'r') as f:
        total_population_csv = csv.reader(f)

        line_count = 0
        for row in total_population_csv:
            if line_count > 0:
                country_name = find_code_from_country(row[0].strip())
                if country_name:
                    if country_name in country_pop_map:
                        country_pop_map[country_name] = country_pop_map[country_name] + int(row[-1])
                    else:
                        country_pop_map[country_name] = int(row[-1])

            line_count += 1

    with open('data/internet_percentage.csv', 'r', encoding='utf-8') as f:
        internet_percentage_csv = csv.reader(f)

        line_count = 0
        for row in internet_percentage_csv:
            if line_count > 0:
                country_name = find_code_from_country(row[1].strip())
                if country_name:
                    percentage = -1
                    offset = -3
                    while percentage == -1 and offset > -len(row):
                        try:
                            percentage = float(row[offset])
                        except Exception as e:
                            offset -= 3
                    
                    if percentage != -1:
                        internet_percent_map[country_name] = percentage

            line_count += 1

    # internet_population_total = 0

    for _, code in country_code_map.items():
        if code in country_pop_map and code in internet_percent_map:
            internet_population_dict[code] = int(country_pop_map[code] * internet_percent_map[code] / 100)
            internet_population_total += internet_population_dict[code]

    for code in internet_population_dict:
        internet_total_percent_dict[code] = internet_population_dict[code] / internet_population_total * 100

    print(f"Total internet population: {internet_population_total} in {len(internet_population_dict)} countries")

    with open('data/internet_population_dict.json', 'w') as f:
        json.dump(internet_population_dict, f, indent=4)

    with open('data/internet_total_percent_dict.json', 'w') as f:
        json.dump(internet_total_percent_dict, f, indent=4)

def read_population_files():
    with open('data/internet_population_dict.json', 'r') as f:
        internet_population_dict = json.load(f)

    with open('data/internet_total_percent_dict.json', 'r') as f:
        internet_total_percent_dict = json.load(f)

    for code in internet_population_dict:
        internet_population_total += internet_population_dict[code]

create_population_files()
# read_population_files()

print(f"Number of countries: {len(alexa_json)}")
print("Countries in dataset:", alexa_json.keys())

print(f"Old number of countries: {len(old_alexa_json)}")

new_countries = [country for country in alexa_json if country not in old_alexa_json]
print(f"Number of new Alexa Top 50 countries: {len(new_countries)}")
print("New Alexa Top 50 countries:", new_countries)

removed_countries = [country for country in old_alexa_json if country not in alexa_json]
print(f"Number of removed Alexa Top 50 countries: {len(removed_countries)}")
print("Removed Alexa Top 50 countries:", removed_countries)

removed_countries_population = 0
for country in removed_countries:
    removed_countries_population += internet_population_dict[country]

removed_countries_pop_list = sorted([(country, internet_population_dict[country]) for country in removed_countries], key=lambda item: item[1], reverse=True)

print(f"Removed countries led to a reduction of {removed_countries_population} or {removed_countries_population / internet_population_total * 100}% of the Internet population")
print(removed_countries_pop_list)