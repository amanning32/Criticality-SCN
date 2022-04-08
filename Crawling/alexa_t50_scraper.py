# inspired by https://github.com/JustinStals/alexa_scrape/blob/master/alexa_scrape.py

from bs4 import BeautifulSoup
import requests
import traceback
import json
from tqdm import tqdm
from datetime import datetime

def get_sites(country):
    domain = f"https://www.alexa.com/topsites/countries/{country}"

    try:
        response = requests.get(domain)
        soup = BeautifulSoup(response.text, 'html.parser')
    except AttributeError:
        print('Error getting country ' + country)
        return None
    except Exception:
        print(traceback.print_exc())
        return None

    listing_div = soup.find("div", {"class": "listings table"})
    if not listing_div:
        return None

    country_sites = []
    
    for row in listing_div.findAll("div", "tr site-listing"):
        rank = row.find("div", {"class": "td"}).text
        website = row.find("div", {"class", "td DescriptionCell"}).text.strip()
        stats = row.findAll("div", {"class", "td right"})
        website_dict = {"Rank": rank,
                        "Site" : website,
                        "Daily Time on Site" : stats[0].text,
                        "Daily Pageviews per Visitor": stats[1].text,
                        "Percentge of Traffic from Search": stats[2].text,
                        "Total Sites Linking in": stats[3].text}
        
        country_sites.append(website_dict)

    return country_sites

def get_countries():
    domain = "https://www.alexa.com/topsites/countries"

    try:
        response = requests.get(domain)
        soup = BeautifulSoup(response.text, 'html.parser')
    except AttributeError:
        print('Error getting countries')
        return None
    except Exception:
        print(traceback.print_exc())
        return None

    countries = []
    
    for item in soup.findAll("li"):
        link = item.find("a")
        if link:
            countries.append(link['href'].split('/')[1])

    print(countries)

    return countries

data = {}

for country in tqdm(get_countries()):
    data[country] = get_sites(country)

current_day = datetime.today().strftime('%Y%m%d')
print(current_day)

with open(f"alexa_top_50_{current_day}.json", "w") as f:
    json.dump(data, f, indent='\t')