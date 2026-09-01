---
name: maps
description: Geocode, POIs, routes, timezones via OpenStreetMap/OSRM.
version: 1.2.0
author: Mibayy
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [maps, geocoding, places, routing, distance, directions, nearby, location, openstreetmap, nominatim, overpass, osrm]
    category: productivity
    requires_toolsets: [terminal]
    supersedes: [find-nearby]
---

# Maps

role: OpenStreetMap/OSRM location-intelligence operator
do: geocode/reverse; find nearby POIs; route/distance/directions; resolve timezone; query area/bbox; present tap-to-open links
inputs: place/address/coordinates/location pin, category/radius, origin/destination, mode, bbox
outputs: coordinates/address, POIs/tags/links, road+straight-line distance, duration/steps, timezone/offset/local time, bbox/area
¬: API key/install requirement (stdlib only); ignore Nominatim rate/ToS; treat OSM hours as authoritative; confuse `--to` destination; infer precise current availability from community data

Data: OpenStreetMap/Nominatim, Overpass API, OSRM, TimeAPI.io. Stated scope:
8 commands, 44 POI categories, zero dependencies, no API key. Supersedes
`find-nearby`; `nearby` keeps `--near "<place>"` and multi-category support.

## When to Use

- Telegram location pin → `nearby`
- place → coordinates → `search`; coordinates → address → `reverse`
- nearby restaurant/hospital/pharmacy/hotel → `nearby`
- travel distance/time → `distance`; turn-by-turn → `directions`
- timezone → `timezone`; geographic area → `area` + `bbox`

## Procedure

1. Resolve the script + concrete place/coordinates/pin, category, radius, or route.
2. Choose one command below; geocode addresses before coordinate-only operations.
3. Run with bounded limit/radius/bbox and respect Nominatim/Overpass policies.
4. Report source coordinates, tags, distance/time/offset, and uncertainty.
5. Complete Verification; never infer real-time availability from OSM alone.

## Prerequisites

Python 3.8+ stdlib only. Script: `~/.hermes/skills/maps/scripts/maps_client.py`.

```bash
MAPS=~/.hermes/skills/maps/scripts/maps_client.py
```

## Commands

### search — geocode

```bash
python $MAPS search "Eiffel Tower"
python $MAPS search "1600 Pennsylvania Ave, Washington DC"
```

Returns lat/lon, display name, type, bounding box, importance.

### reverse — coordinates → address

```bash
python $MAPS reverse 48.8584 2.2945
```

Returns street/city/state/country/postcode breakdown.

### nearby — category search

```bash
# By coordinates (from a Telegram location pin, for example)
python $MAPS nearby 48.8584 2.2945 restaurant --limit 10
python $MAPS nearby 40.7128 -74.0060 hospital --radius 2000

# By address / city / zip / landmark — --near auto-geocodes
python $MAPS nearby --near "Times Square, New York" --category cafe
python $MAPS nearby --near "90210" --category pharmacy

# Multiple categories merged into one query
python $MAPS nearby --near "downtown austin" --category restaurant --category bar --limit 10
```

Categories:

restaurant, cafe, bar, hospital, pharmacy, hotel, guest_house, camp_site,
supermarket, atm, gas_station, parking, museum, park, school, university,
bank, police, fire_station, library, airport, train_station, bus_stop, church,
mosque, synagogue, dentist, doctor, cinema, theatre, gym, swimming_pool,
post_office, convenience_store, bakery, bookshop, laundry, car_wash,
car_rental, bicycle_rental, taxi, veterinary, zoo, playground, stadium,
nightclub.

Each result: `name`, `address`, `lat`/`lon`, `distance_m`, `maps_url`,
`directions_url`, promoted tags `cuisine`, `hours` (`opening_hours`), `phone`,
`website` when available.

### distance — road + straight-line

```bash
python $MAPS distance "Paris" --to "Lyon"
python $MAPS distance "New York" --to "Boston" --mode driving
python $MAPS distance "Big Ben" --to "Tower Bridge" --mode walking
```

Modes: driving default, walking, cycling. Returns road distance/duration +
straight-line comparison.

### directions — turn-by-turn

```bash
python $MAPS directions "Eiffel Tower" --to "Louvre Museum" --mode walking
python $MAPS directions "JFK Airport" --to "Times Square" --mode driving
```

Returns numbered instruction, distance, duration, road, maneuver type.

### timezone

```bash
python $MAPS timezone 48.8584 2.2945
python $MAPS timezone 35.6762 139.6503
```

Returns timezone, UTC offset, current local time.

### area — place bbox

```bash
python $MAPS area "Manhattan, New York"
python $MAPS area "London"
```

Returns bbox, width/height km, approximate area; useful for `bbox`.

### bbox — rectangle POIs

```bash
python $MAPS bbox 40.75 -74.00 40.77 -73.98 restaurant --limit 20
```

Use `area` first for named place coordinates.

## Telegram Location Pins

Extract `latitude:`/`longitude:` and pass directly:

```bash
# User sent a pin at 36.17, -115.14 and asked "find cafes nearby"
python $MAPS nearby 36.17 -115.14 cafe --radius 1500
```

Present numbered names/distances + `maps_url`. For “open now?”, inspect
`hours`; missing/unclear → `web_search` because OSM hours are community-maintained.

## Workflow Examples

- Italian near Colosseum: `nearby --near "Colosseum Rome" --category restaurant --radius 500`
- location pin: extract lat/lon; `nearby LAT LON cafe --radius 1500`
- walk hotel → conference: `directions "Hotel Name" --to "Conference Center" --mode walking`
- downtown Seattle restaurants: `area "Downtown Seattle"`; then `bbox S W N E restaurant --limit 30`

## Pitfalls

- Nominatim ToS max 1 req/s (script handles)
- `nearby` needs coordinates or `--near "<address>"`
- OSRM coverage best Europe/North America
- Overpass peak latency; script fallback: overpass-api.de → overpass.kumi.systems
- `distance`/`directions` destination uses `--to`, not positional
- ambiguous global zip → add country/state

## Verification

```bash
python ~/.hermes/skills/maps/scripts/maps_client.py search "Statue of Liberty"
# Should return lat ~40.689, lon ~-74.044

python ~/.hermes/skills/maps/scripts/maps_client.py nearby --near "Times Square" --category restaurant --limit 3
# Should return a list of restaurants within ~500m of Times Square
```

- [ ] coordinates/place and command mode are explicit
- [ ] route result includes road distance/duration and source caveats
- [ ] POI result includes names/distances/links; hours caveat stated
- [ ] rate limits/fallbacks/coverage and ambiguous geocoding handled