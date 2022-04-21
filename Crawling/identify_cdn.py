import json
from tqdm import tqdm
import requests
import socket
import ipaddress

# UNTESTED AND NOT CONNECTED TO WORKFLOW!!!

def identify_cdn(ip_list): 
    cdn_map = {}
    rdns = {}
    failed_list = []
    Other = []

    # populate CDN map, so we don't lose anyone
    for ip in ip_list:
        cdn_map[ip] = 'N/A'

    # rDNS to get hostname
    for ip in tqdm(ip_list, desc="rDNS Step"):
        try:
            reversed_dns = socket.gethostbyaddr(ip)
            rdns[ip] = []
            rdns[ip].append(reversed_dns[0])
            for alias in reversed_dns[1]:
                rdns[ip].append(alias)
            # print(rdns[ip])
        except socket.herror:
            # print("Unknown")
            Other.append(ip)

    # match hostname to CDN format
    for ip in tqdm(rdns, "Hostname matching step"):
        match = False
        for r in rdns[ip]:
            if "amazon" in r or "aws" in r:
                cdn_map[ip] = 'Amazon/AWS'
                match = True
                break
        for r in rdns[ip]:
            if r.endswith("1e100.net"):
                cdn_map[ip] = 'Google'
                match = True
                break
        for r in rdns[ip]:
            if r.endswith("cloudfront.net"):
                cdn_map[ip] = 'CloudFront'
                match = True
                break
        if not match:
            Other.append(ip)
    
    # identify Azure hosts
    azure_ip = []
    with open("../Geolocation/serv_data/azure_ip_ranges.json", 'r') as fp:
        azure_ip = json.load(fp)

    for ip in tqdm(Other, desc="Microsoft matching step"):
        found = False
        try:
            for (prefix, _) in azure_ip.items():
                net = ipaddress.ip_network(prefix)
                if ipaddress.ip_address(ip) in net:
                    found = True
                    cdn_map[ip] = 'Microsoft'
                    break
        except:
            break
        if not found:
            failed_list.append(ip)

    no_cdn_list = []

    whatsmycdn_cdns = ['Cloudflare', 'Edgecast', 'Fastly', 'Incapsula']
    
    for ip in tqdm(failed_list, desc="WhatsMyCDN step"):
        for cdn in whatsmycdn_cdns:
            try:
                whatsmycdn_url = f'https://api.whatsmycdn.com/is{cdn}IP?ip={ip}'
                r = requests.get(whatsmycdn_url, timeout=5)
                if r.status_code == 200:
                    text = json.loads(r.text)
                    if "NOT" not in text['message']:
                        cdn_map[ip] = cdn
                        break
            except Exception as e:
                print(f"Error getting {ip} on WhatsMyCDN: {e}")
            
            no_cdn_list.append(ip)
    
    print(f"Total number of ips: {len(ip_list)}. Number not matched to a CDN: {len(no_cdn_list)}")