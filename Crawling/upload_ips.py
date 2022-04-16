from pymongo import MongoClient
import json
from tqdm import tqdm
import argparse

# Set up MongoDB connection
mongo_config = None
with open("../config.json", 'r') as fp:
    mongo_config = json.load(fp)["mongo_str"]
mongo_client = MongoClient(mongo_config)

# Upload IPs.
# db (str): Name of MongoDB database to upload IPs to. Expect/create a collection named "ips"
# source_file (str): name of JSON file containing country-associated IPs.
#                    of the form { country: {IP: {CDN: N/A, status: new}}}
#                    That format is provided from (TODO) function
# Output: none; side-effect of uploading IPs to MongoDB.
def upload_ips(db: str, source_file: str) -> None:
    ip_table = mongo_client[db]['ips']
    print(ip_table.find())

    ip_json = None

    with open(source_file) as f:
        ip_json = json.load(f)

    for country in tqdm(ip_json, desc="Countries:"):
        for entry in tqdm(ip_json[country], desc="Current country:"):
            ip_json[country][entry]['country'] = country
            ip_json[country][entry]['ip'] = entry
            print(ip_json[country][entry])
            ip_table.insert_one(ip_json[country][entry])

    print(ip_table.find())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Uploading IPs')
    parser.add_argument('-d', type=str, required=True, help="Name of the MongoDB database")
    parser.add_argument('-f', type=str, required=True, help="Name of JSON file containing country-associated IPs")

    args = parser.parse_args()

    db = args.d
    source_file = args.f

    upload_ips(db, source_file)