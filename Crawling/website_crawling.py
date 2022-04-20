from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager

import tldextract
import socket
import os

import json

import argparse
from tqdm import tqdm

# Constants: filename to read/write from (locally) and source of Alexa Top 50 data
country_ip_filename = 'country_ips.json'
alexa_filename = 'alexa_top_50_20220407.json'

country_ip_json = {}

def crawl_sites(driver, websites: list) -> list:
    ip_addresses = set()

    for website in tqdm(websites):
        urls = set()

        try:
            website_string = 'http://www.' + website.lower().strip()
            driver.get(website_string)
            entries = driver.execute_script("var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network;")

            for item in entries:
                # get domain name
                core_url = tldextract.extract(item['name'])
                core_url_string = '.'.join(core_url).strip()

                # remove empty subdomain
                if core_url_string[0] == '.':
                    core_url_string = core_url_string[1:]
                
                # filter out non-urls
                if core_url_string[-1] != '.':
                    urls.add(core_url_string)
        except Exception as e:
            print(f"Error loading webpage {website}: {e}", flush=True)

        for url in urls:
            try:
                dns_result = socket.gethostbyname(url)
                ip_addresses.add(dns_result)
            except Exception as e:
                print(f"Error resolving hostname for {url}: {e}", flush=True)

    return list(ip_addresses)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Alexa Top 50 Websites Crawling')
    parser.add_argument('-c', type=str, required=True, help="Country Code of country to crawl")

    args = parser.parse_args()

    country = args.c

    # load country domains
    alexa_websites = None

    with open(alexa_filename, 'r') as f:
        alexa_websites = json.load(f)

    if country not in alexa_websites:
        print(f"Country {country} not found in Alexa websites; aborting")
        exit()
    
    country_websites = []
    for entry in alexa_websites[country]:
        country_websites.append(entry['Site'])

    # load existing data
    if os.path.exists(country_ip_filename):
        with open(country_ip_filename, 'r') as f:
            country_ip_json = json.load(f)

    # scrape the index page
    profile = webdriver.FirefoxProfile()
    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    
    new_ips = crawl_sites(driver, country_websites)

    # update JSON
    country_ip_json[country] = new_ips

    with open(country_ip_filename, 'w') as f:
        json.dump(country_ip_json, f, indent=4)

    driver.quit()
    
    print(f"Website crawling for {country} complete!")