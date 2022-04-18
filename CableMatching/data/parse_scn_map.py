import os, json
import requests
from tqdm import tqdm

path_to_scn = "../../../www.submarinecablemap.com/web/public/api/v3/cable"

bing_api_key = None
country_code_map = None

with open("../../config.json", 'r') as f:
    config = json.load(f)
    bing_api_key = config["bing_api"]

with open("../../Geolocation/serv_data/country_name_code.json", 'r') as f:
    country_code_map = json.load(f)

def find_country_code(country: str):
    if country in country_code_map:
        return country_code_map[country]
    else:
        for key in country_code_map:
            if country in key:
                return country_code_map[key]

def create_scn_map_json():
    scn_map_json = []

    for filename in tqdm(os.listdir(path_to_scn), desc="Cable JSON files"):
        # skip the full list! (It doesn't have landings info, which we need for geolocation)
        if filename == "all.json" or filename == "cable-geo.json":
            continue
        
        cable_json = None

        try:
            with open(os.path.join(path_to_scn, filename), 'r') as f:
                cable_json = json.load(f)

            if not cable_json['is_planned']:
                current_cable = {}
                current_cable['name'] = cable_json['name']
                current_cable['owners'] = cable_json['owners']
                current_cable['landings'] = []
                current_cable['landings_latlng'] = []
                current_cable['rfs'] = cable_json['rfs']
                current_cable['length'] = cable_json['length']

                for landing in cable_json['landing_points']:
                    if not landing['is_tbd']:
                        num_commas = landing['name'].count(',')
                        bing_url = None

                        # City, Country
                        if num_commas == 1:
                            city, country = landing['name'].split(',')
                            country = find_country_code(country.strip())
                            bing_url = f"http://dev.virtualearth.net/REST/v1/Locations?countryRegion={country}&locality={city}&key={bing_api_key}"
                            # print(bing_url)

                        # City, Region, Country
                        elif num_commas == 2:
                            city, region, country = landing['name'].split(',')
                            region = region.strip()
                            country = find_country_code(country.strip())
                            bing_url = f"http://dev.virtualearth.net/REST/v1/Locations?countryRegion={country}&adminDistrict={region}&locality={city}&key={bing_api_key}"
                            # print(bing_url)

                        # one case: Kihei, Maui, HI, United States (City, Sub-region, Region, Country)
                        elif num_commas == 3:
                            city, subregion, region, country = landing['name'].split(',')
                            region = region.strip()
                            country = find_country_code(country.strip())
                            bing_url = f"http://dev.virtualearth.net/REST/v1/Locations?countryRegion={country}&adminDistrict={region}&locality={city}&key={bing_api_key}"
                        else:
                            print(f"Unknown landing location format: {landing['name']} for cable {current_cable['name']}")
                            continue
                        
                        r = requests.get(bing_url, timeout=5)

                        resp_json = json.loads(r.text)
                        if resp_json['statusCode'] == 200:
                            current_cable['landings'].append(landing['name'])
                            current_cable['landings_latlng'].append(resp_json['resourceSets'][0]['resources'][0]['point']['coordinates'])

                            
                scn_map_json.append(current_cable)
        except Exception as e:
            print(f"Error for {filename} with exception {e}")
    
    with open('submarine_cable_map_NEW.json', 'w') as f:
        json.dump(scn_map_json, f, indent=4)

create_scn_map_json()

