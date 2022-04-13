import json
from tqdm import tqdm

# Pre-process AWS IPs.
# Input: aws_ip_ranges (string): File containing AWS IP ranges (provided aws_ip_ranges.json)
#        old_aws_ip_ranges (string): Filename containing old AWS IP ranges to compare to (provided OLD_aws_locations.json))
# Output: prints all current AWS regions, the number of AWS regions, the number of old AWS regions, and each new AWS region
def aws_regions_compute(aws_ip_ranges: str, old_aws_locations: str) -> None:
    # Build the list of all current regions.
    regions = set()

    aws_ips = None

    with open(aws_ip_ranges, 'r') as f:
        aws_ips = json.load(f)

    for prefix in aws_ips["prefixes"]:
        regions.add(prefix["region"])

    # Statistics.
    print("AWS regions:", regions)
    print("Number of AWS regions: ", len(regions))

    old_locations = None

    with open(old_aws_locations, 'r') as f:
        old_locations = json.load(f)

    print("Number of old AWS regions: ", len(old_locations))

    print("New AWS regions:")

    for region in regions:
        if region not in old_locations:
            print(region)
    
    # Write locations to file, to create locations manually.
    with open("aws_locations_NEW.json", 'w') as f:
        json.dump(sorted(regions), f, indent=4)


def azure_regions_compute(azure_ip_ranges: str, old_azure_locations: str) -> None:
    # Build the list of current regions, as well as current IPs.
    azure_input = None

    with open(azure_ip_ranges, 'r') as f:
        azure_input = json.load(f)

    azure_ips = {}

    # Filter out "locations" that are not locations. Note the lowercase.
    azure_services_as_locations = ['backend', 'core', 'firstparty', 'frontend', 'serviceendpoint']
    azure_locations = set()

    for value in tqdm(azure_input['values']):
        # catches names of the form SERVICE.LOCATION (except example above)
        if "." in value['name']:
            location = value['name'].split('.')[1].lower()

            # don't keep track of non-locations
            if location not in azure_services_as_locations:
                azure_locations.add(location)
            
            for located_ip in value['properties']['addressPrefixes']:
                # filter out IPv6 addresses
                if ':' not in located_ip:
                    # write location if it is a location
                    if location not in azure_services_as_locations:
                        azure_ips[located_ip] = location
                    else:
                        azure_ips[located_ip] = "N/A"
        else:
            for located_ip in value['properties']['addressPrefixes']:
                # filter out IPv6 addresses, and don't overwrite locations in case of duplicates
                if ':' not in located_ip and located_ip not in azure_ips:
                    azure_ips[located_ip] = "N/A"

    # Statistics
    print("Azure locations: ", azure_locations)
    print("Number of Azure locations: ", len(azure_locations))

    old_regions = None

    with open(old_azure_locations, 'r') as f:
        old_regions = json.load(f)

    print("Number of old Azure regions:", len(old_regions))

    print("New Azure regions:")

    for location in azure_locations:
        if location not in old_regions:
            print(location)

    # Write IPs & region to file.
    with open("azure_ip_ranges.json", 'w') as f:
        json.dump(azure_ips, f, indent=4)

    # Write regions to file, to create region locations manually.
    with open("azure_region_locations_NEW.json", 'w') as f:
        json.dump(sorted(azure_locations), f, indent=4)
            
aws_regions_compute("aws_ip_ranges.json", "OLD_aws_locations.json")
azure_regions_compute("ServiceTags_Public_20220404.json", "OLD_azure_region_locations.json")