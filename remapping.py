import os
from mapping import generate_ip_map

def main():
    root = os.path.dirname(__file__)
    # Iterate over country directories
    for country in os.listdir(root):
        country_path = os.path.join(root, country)
        print(f"Processing country: {country}")
        if not os.path.isdir(country_path):
            continue
        try:
            txt = os.path.join(country_path, "IPaddressesMODIFIED.txt")
            js = os.path.join(country_path, "ipapi_output.json")
            gpkg = os.path.join(root, "gadm_410-levels.gpkg")

            # Admin level 0 map
            out0 = os.path.join(country_path, f"admin0_{country}.html")
            generate_ip_map(txtfilepath=txt,
                            jsonfilepath=js,
                            geo_package=gpkg,
                            admin_level=0,
                            output_html=out0)

            # Admin level 1 map
            out1 = os.path.join(country_path, f"admin1_{country}.html")
            generate_ip_map(txtfilepath=txt,
                            jsonfilepath=js,
                            geo_package=gpkg,
                            admin_level=1,
                            output_html=out1)

            # Admin level 2 fixed styling map
            out2 = os.path.join(country_path, f"admin2_fixed_{country}.html")
            generate_ip_map(txtfilepath=txt,
                            jsonfilepath=js,
                            geo_package=gpkg,
                            admin_level=2,
                            output_html=out2)
        except FileNotFoundError as e:
            print(f"File not found: {e}")
            continue
        except Exception as e:
            print(f"Error processing {country}: {e}")
            continue
        print(f"Generated maps for {country}")
    print("All maps generated successfully.")


if __name__ == "__main__":
    main()
