# WiCaSa — Wikipedia Category Scraper and Analyzer

**Roo Case** | CS304

Code available at: https://github.com/RooCase/WiCaSa

---

## Overview

WiCaSa is a research tool for analyzing the geographic origins of unregistered (IP-based) Wikipedia edits to political content. It answers two questions:

- What countries do edits to pages under a given country's political Wikipedia categories come from? Do unregistered users mostly edit from within or outside that country?
- What cities or regions are most associated with edits to political pages? Are there notable exceptions beyond major population centers?

The project covers seven countries: **Australia, Canada, China, India, North Korea, the United Kingdom, and the United States**. Edit data was collected for the period **January 1, 2023 – December 31, 2024**.

---

## How It Works

The pipeline has four stages:

1. **Category crawling** (`mediawiki_request.py`) — Starting from a top-level Wikipedia category (e.g. `Category:Politics_of_Canada`), the Wikipedia API is queried recursively up to three subcategory levels deep. Article titles are written to `temp.txt`.

2. **Revision collection** (`mediawiki_request.py`) — For each article, the Wikipedia API is queried for all revisions in the date range. Only revisions by unregistered (IP-address) users are kept. IP addresses are written to `IPaddresses.txt`.

3. **Geolocation** (`IP_Data.py`) — Duplicate IPs are removed and the unique list is saved to `IPaddressesMODIFIED.txt`. IP geolocation is resolved in batches via the [ipinfo.io](https://ipinfo.io) API, and results are saved to `ipapi_output.json`.

4. **Mapping** (`mapping.py` / `remapping.py`) — IP counts are spatially joined against GADM administrative boundaries and rendered as interactive choropleth or circle-marker HTML maps at three administrative levels (country, state/region, county/district).

`main.py` runs the full pipeline for a single country. `remapping.py` re-generates maps for all countries without re-fetching data.

---

## Setup

### Dependencies

```
pip install requests geopandas pandas folium shapely fiona branca
```

### API Key

An [ipinfo.io](https://ipinfo.io) API key is required for geolocation. Set it in [IP_Data.py](IP_Data.py):

```python
API_KEY = "(INPUT YOUR API KEY HERE)"
```

### GADM Data

Download the GADM 4.1 GeoPackage (`gadm_410-levels.gpkg`) from [gadm.org](https://gadm.org) and place it in the project root. This file is not included in the repository due to its size.

---

## Usage

**Full pipeline for one country:**

Edit the `category`, `start_time`, and `end_time` variables at the top of [main.py](main.py), then run:

```bash
python main.py
```

Output files will be written to the working directory. Move them into the appropriate country folder when done.

**Re-generate maps from existing data (all countries):**

```bash
python remapping.py
```

This iterates over all country folders and regenerates the three HTML maps for each one without making any API calls.

---

## Repository Structure

```
WiCaSa/
├── main.py                # Full pipeline runner (single country)
├── remapping.py           # Batch map re-generator (all countries)
├── mediawiki_request.py   # Wikipedia API: category crawl + revision fetch
├── IP_Data.py             # IP deduplication + ipinfo.io geolocation
├── mapping.py             # GADM spatial join + Folium map generation
├── gadm_410-levels.gpkg   # GADM boundary data (not in repo — download separately)
│
├── Australia/
├── Canada/
├── China/
├── India/
├── North Korea/
├── UK/
└── USA/
```

Each country folder contains:

| File | Description |
|---|---|
| `admin0_{country}.html` | Interactive choropleth map at the **country** level (admin 0) |
| `admin1_{country}.html` | Interactive circle map at the **state / administrative region** level (admin 1) |
| `admin2_{country}.html` | Interactive circle map at the **county / district** level (admin 2) |
| `admin2_fixed_{country}.html` | Older admin-2 map with different formatting, kept for reference |
| `IPaddresses.txt` | Raw list of all IP addresses pulled from Wikipedia revisions |
| `IPaddressesMODIFIED.txt` | Deduplicated IP list (one entry per unique IP) |
| `ipapi_output.json` | Geolocation data for each unique IP, from ipinfo.io |
| `RevisionJSON.json` | Full revision history returned from the Wikipedia API |
| `temp.txt` | All article titles found up to 3 subcategory levels deep |

---

## Notes

- Only **unregistered (IP-based)** edits are collected. Registered-user edits are excluded.
- The Wikipedia API returns at most `rvlimit=max` revisions per request; continuation tokens are followed automatically.
- CIDR-range IPs (e.g. `192.0.2.0/24`) that occasionally appear in Wikipedia revision data are expanded to individual addresses by `mediawiki_request.CIDRIP()`, though the main pipeline filters these out at the IP-validation step in `IP_Data.refine_ip_addresses()`.
- ipinfo.io batch requests are capped at 1,000 IPs per call; `IP_Data.batch_ipapi()` chunks larger lists automatically.
