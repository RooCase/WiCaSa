import json
import requests
import geopandas as gpd
import pandas as pd
import folium
from shapely.geometry import Point
import fiona
from collections import Counter
from branca.colormap import linear

API_KEY = "(INPUT YOUR API KEY HERE)"

def refine_ip_addresses(txtfilepath):
    """
    This function reads a text file containing IP addresses, refines them, and returns a list of unique IP addresses.
    """
    try:
        with open(txtfilepath, 'r') as file:
            ip_addresses = file.readlines()
        
        # Remove whitespace and duplicates
        ip_addresses = list(set(ip.strip() for ip in ip_addresses))
        
        # Filter out invalid IP addresses
        valid_ip_addresses = [ip for ip in ip_addresses if is_valid_ip(ip)]
        
        return valid_ip_addresses
    except Exception as e:
        print(f"Error: {e}")
        return []
    
def is_valid_ip(ip):
    """
    This function checks if a given IP address is valid.
    """
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or not (0 <= int(part) <= 255):
                return False
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def batch_ipapi(ip_list):
    """
    This function takes a list of IP addresses and returns their geolocation data using the ipinfo.io API. It batches the requests in groups of 1000 to avoid hitting the API rate limit.
    """
    try:
        # Split the list into chunks of n
        chunks = [ip_list[i:i + 1000] for i in range(0, len(ip_list), 1000)]
        results = []
        
        for chunk in chunks:
            print(f"Processing chunk of {len(chunk)} IPs...")
            response = requests.post('https://ipinfo.io/batch', json=chunk, headers={'Authorization': ('Bearer ' + API_KEY)})
            response.raise_for_status()
            api_result = response.json()
            results.append(api_result)
        
        print(f"Processed {len(results)} geolocation records.")
        # print(results)
        return results
    except (requests.HTTPError, ValueError) as e:
        print(f"Error: {e}")
        return []



def ipapi(ip):
    try:
        response = requests.post('https://ipinfo.io/batch', json=ip, headers={'Authorization': ('Bearer ' + API_KEY)})
        response.raise_for_status()
        return response.json()
    except (requests.HTTPError, ValueError) as e:
        print(f"Error: {e}")
        return {}