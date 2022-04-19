import os, json
import requests
from tqdm import tqdm

path_to_scn = "../../../www.submarinecablemap.com/web/public/api/v3/cable"

bing_api_key = None
country_code_map = None

with open("../../config.json", 'r') as f:
    config = json.load(f)
    bing_api_key = config["bing_api"]

with open("../../Geolocation/serv_data/country_name_code.json", 'r', encoding='utf-8') as f:
    country_code_map = json.load(f)

# I was having Unicode encoding problems; this is my 'manual' fix.
country_code_accent_map = {
    b'R\xc3\x83\xc2\xa9union': 'RE',
    b"C\xc3\x83\xc2\xb4te d'Ivoire": 'CI',
    b'Cura\xc3\x83\xc2\xa7ao': 'CW',
    b'Saint Barth\xc3\x83\xc2\xa9lemy': "BL"
}

def find_country_code(country: str) -> str:
    if country.encode('utf-8') in country_code_accent_map:
        return country_code_accent_map[country.encode('utf-8')]

    if country in country_code_map:
        return country_code_map[country]
    else:
        for key in country_code_map:
            if country in key:
                return country_code_map[key]
    print(f"No country code found for {country} with length {len(country)}", flush=True)
    return None

def create_scn_map_json() -> None:
    ### As of April 18th, 2022, this does not work for the following cables:
    # bt-mt-1.json: Groudle Bay, Isle of Man not on Bing
    # eastern-caribbean-fiber-system-ecfs.json: Saint Maarten, Sint Maarten not on Bing
    # havhingstenceltixconnect-2-cc-2.json: Port Grenaugh, Isle of Man not on Bing
    # lanis-1.json: Port Grenaugh, Isle of Man not on Bing
    # saba-statia-cable-system-sscs.json: Great Bay Beach, Sint Maarten not on Bing

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

                        # City, Country; or City, Congo, [Dem. Rep./Rep.]
                        if num_commas == 1 or "Congo" in landing['name']:
                            city, country = landing['name'].split(',', 1)
                            country = find_country_code(country.strip())
                            bing_url = f"http://dev.virtualearth.net/REST/v1/Locations?countryRegion={country}&locality={city}&key={bing_api_key}"

                        # City, Region, Country
                        elif num_commas == 2:
                            city, region, country = landing['name'].split(',')
                            region = region.strip()
                            country = find_country_code(country.strip())
                            bing_url = f"http://dev.virtualearth.net/REST/v1/Locations?countryRegion={country}&adminDistrict={region}&locality={city}&key={bing_api_key}"

                        # one case: Kihei, Maui, HI, United States (City, Sub-region, Region, Country)
                        elif num_commas == 3:
                            city, subregion, region, country = landing['name'].split(',')
                            region = region.strip()
                            country = find_country_code(country.strip())
                            bing_url = f"http://dev.virtualearth.net/REST/v1/Locations?countryRegion={country}&adminDistrict={region}&locality={city}&key={bing_api_key}"
                        else:
                            print(f"Unknown landing location format: {landing['name']} for cable {current_cable['name']}", flush=True)
                            continue
                        
                        r = requests.get(bing_url, timeout=5)

                        resp_json = json.loads(r.text)
                        if resp_json['statusCode'] == 200:
                            current_cable['landings'].append(landing['name'])
                            current_cable['landings_latlng'].append(resp_json['resourceSets'][0]['resources'][0]['point']['coordinates'])

                            
                scn_map_json.append(current_cable)
        except Exception as e:
            print(f"Error for {filename} with exception {e}", flush=True)
    
    with open('submarine_cable_map_NEW.json', 'w') as f:
        json.dump(scn_map_json, f, indent=4)

def get_new_cables(old_map: str, new_map: str) -> None:
    old_json = None
    new_json = None

    with open(old_map, 'r') as f:
        old_json = json.load(f)

    with open(new_map, 'r') as f:
        new_json = json.load(f)

    old_cables = set()
    new_cables = set()

    for element in old_json:
        old_cables.add(element['name'])
    for element in new_json:
        if element['name'] in old_cables:
            old_cables.remove(element['name'])
        else:
            new_cables.add(element['name'])
    
    print(f"There are {len(old_cables)} old cables not included (incl. name differences & retired cables):")
    print(sorted(old_cables))
    print(f"There are {len(new_cables)} new cables (incl. name differences):")
    print(sorted(new_cables))

def create_country_cable(scn_map_file: str) -> None:
    scn_map = None
    country_cables = {}
    country_cable_hops = {}

    with open(scn_map_file, 'r') as f:
        scn_map = json.load(f)

    for cable in tqdm(scn_map, desc="Submarine cables"):
        previous_landings = []
        for i in range(len(cable['landings'])):
            landing = cable['landings'][i]

            # country (or unique substring, i.e. Congos) is always at the end
            country = landing.split(',')[-1].strip()
            country_code = find_country_code(country)

            # create country_cable
            if country_code not in country_cables:
                country_cables[country_code] = []
            
            if cable['name'] not in country_cables[country_code]:
                country_cables[country_code].append(cable['name'])

            # create country_hop_cable -- all pairs of landings
            for last_landing in previous_landings:
                if last_landing != country_code:
                    # add for one direction
                    hop = last_landing + '-' + country_code

                    if hop not in country_cable_hops:
                        country_cable_hops[hop] = []
                    
                    country_cable_hops[hop].append(cable)

                    # ...and add for other direction
                    hop = country_code + '-' + last_landing

                    if hop not in country_cable_hops:
                        country_cable_hops[hop] = []
                    
                    country_cable_hops[hop].append(cable)
            
            previous_landings.append(country_code)
    
    print(f"There are submarine cable landings in {len(country_cables)} countries")
    print(f"There are {int(len(country_cable_hops) / 2)} unique country hops via submarine cables")

    with open('country_cable_NEW.json', 'w') as f:
        json.dump(country_cables, f, indent=4)
    with open('country_hop_cable_NEW.json', 'w') as f:
        json.dump(country_cable_hops, f, indent=4)

create_scn_map_json()
get_new_cables('submarine_cable_map_OLD.json', 'submarine_cable_map.json')
create_country_cable('submarine_cable_map.json')