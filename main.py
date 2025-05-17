import IP_Data, mapping, mediawiki_request, json

if __name__ == "__main__":
    category = "Politics_of_Canada"
    start_time = "2024-12-31T23:59:59Z"  # Newer
    end_time = "2023-01-01T00:00:00Z"    # Older
    tempfile = "temp.txt"
    mappingAdminlevel = 2

    # Wipe the file if it exists
    try:
        with open(tempfile, "w") as f:
            f.write("")
    except FileNotFoundError:
        pass 

    articles = mediawiki_request.get_all_all_articles(category, max_depth=3, file_path=tempfile)

    revisions = []
    # Remove duplicates from the list of articles
    articles = mediawiki_request.remove_duplicates(mediawiki_request.read_existing_articles(tempfile))

    for article in articles: 
        if article.startswith("Category:") \
           or article.startswith("File:") \
           or article.startswith("Template:") \
           or article.startswith("Wikipedia:") \
           or article.startswith("User:") \
           or article.startswith("Help:"):
            # Skip categories and other namespaces 
            print(f"Skipping category: {article}")
            continue
    rev = mediawiki_request.get_revision_history(articles, start_time, end_time, ip_only=True)
    revisions.append(rev)

    print("Revision history complete. Now writing to file...")
    with open("RevisionJSON.json", "w") as f:
        json.dump(revisions, f, indent=4)
    
    # Read and refine IP addresses
    print("Refining IP addresses...")
    ipaddresses = IP_Data.refine_ip_addresses(txtfilepath="IPaddresses.txt")
    
    with open("IPaddressesMODIFIED.txt", "w") as f:
        for ip in ipaddresses:
            f.write(ip + "\n")
    
    # with open("IPaddressesMODIFIED.txt", "r") as f:
    #     ipaddresses = f.readlines()


    print("Refining IP addresses complete. Now getting geolocation data...")
    json_location_data = IP_Data.batch_ipapi(ipaddresses)

    with open("ipapi_output.json", "w") as f:
        f.write(json.dumps(json_location_data) + "\n")
        
    print("Geolocation data complete. Now generating map...")
    mapping.generate_ip_map(
        txtfilepath="IPaddresses.txt",
        jsonfilepath="ipapi_output.json",
        geo_package="gadm_410-levels.gpkg",
        admin_level=mappingAdminlevel,
        output_html=f"admin{mappingAdminlevel}_ip_circles_UKPolitics.html"
    )