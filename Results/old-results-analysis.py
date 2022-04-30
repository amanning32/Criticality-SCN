import json, csv

apr_summary_data = {}
apr_bundle_data = {}
sept_summary_data = {}
sept_bundle_data = {}
internet_population_dict = {}
internet_total_percent_dict = {}
internet_population_total = 0
combined_data = {}

with open('APR/country_data.json', 'r') as f:
    apr_summary_data = json.load(f)

with open('SEPT/country_data.json', 'r') as f:
    sept_summary_data = json.load(f)

with open('APR/country_ip_sol_bundles.json', 'r') as f:
    apr_bundle_data = json.load(f)

with open('SEPT/country_ip_sol_bundles.json', 'r') as f:
    sept_bundle_data = json.load(f)

with open('data/internet_population_dict.json', 'r') as f:
    internet_population_dict = json.load(f)

with open('data/internet_total_percent_dict.json', 'r') as f:
    internet_total_percent_dict = json.load(f)

for code in internet_population_dict:
    internet_population_total += internet_population_dict[code]

# fields_to_agg = ['n_ip', 'n_geolocated', 'n_resource', 'n_geolocatedresource', 'n_cdnresource', 'n_cdnmatch', 'n_noncdnresource', 'n_noncdnmatch']

# for code in apr_summary_data:
#     combined_data[code] = {}
#     for field in fields_to_agg:
#         combined_data[code][field] = apr_summary_data[code][field] + sept_summary_data[code][field]

# print(combined_data['MK'])

island = ['AU','CY','GB','ID','IE','JP','NZ','PH','SG','TW']
landlocked = ['AT','BY','CH','CZ','HU','MD','MK','RS','SK']
other = ['AL','AR','BA','BE','BG','BR','CA','CL','CN','CO','CR','DE','DK','EE','FI','FR','GE','GR','HK','HR','IL','IN','IT','KE','KH','KR','LV','MX','MY','NL','NO','PK','PL','PT','RO','RU','SE','SI','TH','TR','UA','US','VN','ZA']

def calc_criticality_index():
    criticality_index = {}
    cdn_criticality_index = {}
    bundle_cdn_criticality_index = {}

    for code in sept_summary_data:
        n_bundle = (sept_summary_data[code]['n_bundle'] if sept_summary_data[code]['n_bundle'] > 0 else 1)
        criticality_index[code] = (sept_summary_data[code]['n_cdnmatch'] + sept_summary_data[code]['n_noncdnmatch']) / sept_summary_data[code]['n_resource'] / n_bundle * 100

        if code in internet_total_percent_dict:
            cdn_criticality_index[code] = sept_summary_data[code]['p_cdnhit'] * 100 * internet_total_percent_dict[code]
            bundle_cdn_criticality_index[code] = cdn_criticality_index[code]

    print(cdn_criticality_index)

    for country in island:
        # Taiwan not in World Bank population data, so it doesn't have the index
        if country != 'TW':
            print('island', country, cdn_criticality_index[country])
    for country in landlocked:
        print('landlocked', country, cdn_criticality_index[country])
    for country in other:
        print('other', country, cdn_criticality_index[country])

def calc_link_criticality():
    critical_links = {}
    multi_bundle_count = 0

    for country in apr_bundle_data:
        for ip in apr_bundle_data[country]:
            for record in apr_bundle_data[country][ip]:
                if len(record['bundle']) > 1:
                    multi_bundle_count += 1
                for bundle in record['bundle']:
                    # print(bundle)
                    if len(bundle['cables']) == 1:
                        link_name = bundle['cables'][0]
                        if link_name not in critical_links:
                            critical_links[link_name] = {}
                        
                        country_pair = [bundle['start']['geolocation']['Code'], bundle['end']['geolocation']['Code']]
                        country_pair = sorted(country_pair)
                        country_pair_string = country_pair[0] + '-' + country_pair[1]
                        
                        if country_pair_string not in critical_links[link_name]:
                            critical_links[link_name][country_pair_string] = 0
                        critical_links[link_name][country_pair_string] += 1
    for country in sept_bundle_data:
        for ip in sept_bundle_data[country]:
            for record in sept_bundle_data[country][ip]:
                if len(record['bundle']) > 1:
                    multi_bundle_count += 1
                for bundle in record['bundle']:
                    # print(bundle)
                    if len(bundle['cables']) == 1:
                        link_name = bundle['cables'][0]
                        if link_name not in critical_links:
                            critical_links[link_name] = {}
                        
                        country_pair = [bundle['start']['geolocation']['Code'], bundle['end']['geolocation']['Code']]
                        country_pair = sorted(country_pair)
                        country_pair_string = country_pair[0] + '-' + country_pair[1]
                        
                        if country_pair_string not in critical_links[link_name]:
                            critical_links[link_name][country_pair_string] = 0
                        critical_links[link_name][country_pair_string] += 1
    
    critical_links = dict(sorted(critical_links.items()))
    critical_links_summary = {}
    critical_links_total = 0
    critical_links_countries = {}

    for link in critical_links:
        critical_links_summary[link] = 0
        for country_pair in critical_links[link]:
            critical_links_summary[link] += critical_links[link][country_pair]
            if country_pair not in critical_links_countries:
                critical_links_countries[country_pair] = 0
            critical_links_countries[country_pair] += critical_links[link][country_pair]
        critical_links_total += critical_links_summary[link]

    critical_links_summary = dict(sorted(critical_links_summary.items(), key=lambda v:v[1], reverse=True))
    critical_links_countries = dict(sorted(critical_links_countries.items(), key=lambda v:v[1], reverse=True))
    print(critical_links)
    print(critical_links_total)
    print(critical_links_summary)
    print(critical_links_countries)

    with open('critical_links_summary.json', 'w') as f:
        json.dump(critical_links_summary, f, indent=4)
    with open('critical_links_countries.json', 'w') as f:
        json.dump(critical_links_countries, f, indent=4)

calc_link_criticality()