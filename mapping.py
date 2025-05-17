import json
from collections import Counter
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import fiona

import folium
from branca.colormap import linear


def generate_ip_map(txtfilepath="IPaddressesMODIFIED.txt",
                    jsonfilepath="ipapi_output.json",
                    geo_package="gadm_410-levels.gpkg",
                    admin_level=2,
                    output_html="admin_ip_circles.html"):
    """
    Generate an IP count map using latitude/longitude from ipapi output.
    - txtfilepath: path to text file with one IP per line (for frequency counts)
    - jsonfilepath: path to JSON file containing a list of geolocation records
    - geo_package: path to GADM GeoPackage file
    - admin_level: administrative level to aggregate (0, 1, 2, etc.)
    - output_html: filename for the output HTML map
    """
    print(f"Starting map generation: admin_level={admin_level}, geo_package={geo_package}, output={output_html}")
    # Load IP frequencies
    ip_counts = Counter(line.strip() for line in open(txtfilepath, 'r') if line.strip())
    print(f"Loaded {len(ip_counts)} IPs from {txtfilepath}")

    # Load ipapi JSON and build mapping dict
    with open(jsonfilepath, 'r') as jf:
        data = json.load(jf)

    mapping_dict = {}
    if isinstance(data, dict):
        # JSON is a dict mapping IP -> record
        mapping_dict = data
    elif isinstance(data, list):
        # If list contains mapping dicts (batch responses), flatten them
        if data and all(isinstance(elem, dict) and all(isinstance(v, dict) for v in elem.values()) for elem in data):
            for elem in data:
                mapping_dict.update(elem)
        else:
            # Otherwise expect a list of individual record dicts
            for rec in data:
                if isinstance(rec, dict) and 'ip' in rec:
                    mapping_dict[rec['ip']] = rec
    print(f"Loaded mapping for {len(mapping_dict)} IPs from {jsonfilepath}")

    # Build DataFrame of points
    rows = []
    for ip, count in ip_counts.items():
        record = mapping_dict.get(ip)
        loc = record.get('loc') if record else None
        if not loc:
            continue
        try:
            lat, lon = map(float, loc.split(','))
        except Exception:
            continue
        rows.append({'ip': ip, 'count': count, 'lat': lat, 'lon': lon})
    print(f"Built rows for {len(rows)} IPs with valid locations")
    if not rows:
        print("No valid IPs with location data; map not generated.")
        return

    df = pd.DataFrame(rows)
    df['geometry'] = df.apply(lambda r: Point(r['lon'], r['lat']), axis=1)
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")
    print(f"Created GeoDataFrame with CRS {gdf.crs} and {len(gdf)} points")

    # Select appropriate GADM layer
    layers = fiona.listlayers(geo_package)
    suffix = f"_{admin_level}"
    layer_name = next((ly for ly in layers if ly.endswith(suffix) or ly.endswith(str(admin_level))), None)
    if not layer_name:
        raise ValueError(f"No admin level {admin_level} layer found in {geo_package}: {layers}")
    print(f"Using GADM layer '{layer_name}' for admin level {admin_level}")
    admin_gdf = gpd.read_file(geo_package, layer=layer_name)

    # Ensure points GeoDataFrame uses the same CRS as admin boundaries
    if gdf.crs != admin_gdf.crs:
        gdf = gdf.to_crs(admin_gdf.crs)
        print(f"Reprojected points to CRS {admin_gdf.crs}")

    # Spatial join and count aggregation
    joined = gpd.sjoin(gdf, admin_gdf, predicate='within', how='left')
    print(f"Spatial join produced {len(joined)} joined records")
    counts = joined.groupby('index_right')['count'].sum()
    admin_gdf['count'] = admin_gdf.index.map(counts).fillna(0)

    nonzero = admin_gdf[admin_gdf['count'] > 0]
    print(f"{len(nonzero)} admin areas have count > 0")
    if nonzero.empty:
        print(f"No IPs mapped at admin level {admin_level}.")
        return

    # Create map
    m = folium.Map(location=[20, 0], zoom_start=2)
    print(" -> Setting up colormap based on counts")
    min_c, max_c = nonzero['count'].min(), nonzero['count'].max()
    colormap = linear.YlOrRd_09.scale(min_c, max_c)
    colormap.caption = f"IP Count per Admin-{admin_level}"
    colormap.add_to(m)

    # If top-level (admin 0), shade polygons in a single color
    if admin_level == 0:
        print(" -> Shading admin level 0 polygons")
        # Simplify polygons to reduce vertex count and speed up rendering
        tol = 1.0  # increased tolerance for faster simplification
        simple_gdf = nonzero.copy()
        # Simplify without topology preservation for speed
        simple_gdf['geometry'] = simple_gdf.geometry.simplify(tol)
        print(f" -> Simplified {len(simple_gdf)} polygons with tolerance {tol}")
        folium.GeoJson(
            simple_gdf.__geo_interface__,
            style_function=lambda feature: {
                'fillColor': colormap(feature['properties']['count']),
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.6,
            }
        ).add_to(m)
        print(f" -> Saving admin level 0 map to {output_html}")
        m.save(output_html)
        print(" -> Map saved. Exiting.")
        return

    print(" -> Adding circle markers for non-zero areas")
    name_field = f"NAME_{admin_level}"
    # Draw circles in ascending order so higher counts are on top
    for _, row in nonzero.sort_values('count').iterrows():
        centroid = row.geometry.centroid
        c = row['count']
        radius = 3 + c ** 0.5
        color = colormap(c)
        popup = f"{row.get(name_field, 'Area')}<br>Count: {c}"
        folium.CircleMarker(
            location=[centroid.y, centroid.x],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=popup
        ).add_to(m)

    print(" -> Saving circle marker map", output_html)
    m.save(output_html)
