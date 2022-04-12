import json

# Pre-process AWS IPs.
# Input: aws_ip_ranges (string): File containing AWS IP ranges (provided aws_ip_ranges.json)
#        old_aws_ip_ranges (string): Filename containing old AWS IP ranges to compare to (provided OLD_aws_locations.json))
# Output: prints all current AWS regions, the number of AWS regions, the number of old AWS regions, and each new AWS region
def aws_regions_compute(aws_ip_ranges: str, old_aws_locations: str) -> None:
    regions = set()

    aws_ips = None

    with open(aws_ip_ranges, 'r') as f:
        aws_ips = json.load(f)

    # print(len(aws_ips["prefixes"]))

    for prefix in aws_ips["prefixes"]:
        regions.add(prefix["region"])

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


aws_regions_compute("aws_ip_ranges.json", "OLD_aws_locations.json")